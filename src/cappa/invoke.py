from __future__ import annotations

import contextlib
import importlib
import inspect
from dataclasses import dataclass, field
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Coroutine,
    Generator,
    Generic,
    Hashable,
    List,
    Mapping,
    Sequence,
    TypeVar,
    Union,
    cast,
)

from typing_extensions import Annotated

from cappa.class_inspect import has_command
from cappa.command import Command
from cappa.output import Exit, Output
from cappa.state import State
from cappa.subcommand import Subcommand
from cappa.type_view import CallableView, Empty, EmptyType, TypeView
from cappa.typing import find_annotations, get_method_class


class SelfType: ...


C = TypeVar("C")
T = TypeVar("T")
InvokeCallable = Callable[..., T]
InvokeCallableSpec = Union[InvokeCallable[T], str]


@dataclass(frozen=True)
class Dep(Generic[T]):
    """Describes the callable required to fulfill a given dependency."""

    callable: InvokeCallableSpec[T]


DepTypes = Union[
    Sequence[InvokeCallableSpec[Any]],
    Mapping[InvokeCallableSpec[Any], Union[Dep[Any], InvokeCallableSpec[Any], Any]],
    None,
]
Self = Annotated[T, SelfType]


class InvokeResolutionError(RuntimeError):
    """Raised for errors encountered during evaluation of invoke dependencies."""


@dataclass
class Resolved(Generic[C]):
    callable: InvokeCallableSpec[C]
    kwargs: dict[str, Any | Resolved[Any]] = field(default_factory=lambda: {})
    args: tuple[Any, ...] = field(default=())
    result: C | EmptyType = Empty

    def call(self, *args: Any, output: Output | None = None):
        with self.get(*args, output=output) as value:
            return value

    @contextlib.contextmanager
    def get(self, *args: Any, output: Output | None = None) -> Generator[C, None, None]:
        """Get the resolved value.

        The value itself is cached in the event it's used as a dependency to more
        than one dependency.
        """
        if self.result is not Empty:
            yield self.result
            return

        with contextlib.ExitStack() as stack:
            # Non-resolved values are literal values that can be recorded directly.
            finalized_kwargs = dict(self.iter_kwargs(is_resolved=False))

            # Resolved values need to be recursed into. In order to handle the
            # wrapping context manager, we need to enter all contexts, and only
            # exit at the end.
            for k, v in self.iter_kwargs(is_resolved=True):
                finalized_kwargs[k] = stack.enter_context(v.get(output=output))

            with self.handle_exit(output):
                callable = cast(Callable[..., Any], self.callable)
                requires_management = inspect.isgeneratorfunction(callable)
                if requires_management:
                    # Yield functions are assumed to be context-maneger style generators
                    # what we just need to wrap...
                    callable = contextlib.contextmanager(callable)

                result = callable(*args, *self.args, **finalized_kwargs)
                is_context_manager = isinstance(
                    result, contextlib.AbstractContextManager
                )

                # And then enter before producing the result.
                if requires_management or is_context_manager:
                    result = stack.enter_context(result)  # pyright: ignore

            self.result = result
            yield result

    @contextlib.asynccontextmanager
    async def get_async(self, output: Output | None = None) -> AsyncGenerator[C, None]:
        """Get the resolved value, in an async context.

        Note, this is the exact same process as in `get`, except with `await`,
        `enter_async_context` and `async with`. There seems to be no way to
        share the logic between the two methods, so they just need to be kept
        in sync :shrug:.
        """
        if self.result is not Empty:
            yield self.result
            return

        async with contextlib.AsyncExitStack() as stack:
            finalized_kwargs = dict(self.iter_kwargs(is_resolved=False))
            for k, v in self.iter_kwargs(is_resolved=True):
                finalized_kwargs[k] = await stack.enter_async_context(
                    v.get_async(output=output)
                )

            with self.handle_exit(output):
                callable = cast(Callable[..., Any], self.callable)
                requires_management = inspect.isasyncgenfunction(callable)
                if requires_management:
                    callable = contextlib.asynccontextmanager(callable)

                result: Any = callable(**finalized_kwargs)
                is_context_manager = isinstance(
                    result, contextlib.AbstractAsyncContextManager
                )

                if requires_management or is_context_manager:
                    result = await stack.enter_async_context(result)  # pyright: ignore
                elif isinstance(result, Coroutine):
                    result = await result  # pyright: ignore

            self.result = result
            yield result

    def iter_kwargs(self, *, is_resolved: bool):
        for k, v in self.kwargs.items():
            if is_resolved == isinstance(v, self.__class__):
                yield k, v

    @classmethod
    @contextlib.contextmanager
    def handle_exit(cls, output: Output | None = None):
        try:
            yield
        except Exit as e:
            if output:  # pragma: no cover
                output.exit(e)
            raise e


def resolve_callable(
    command: Command[Any],
    parsed_command: Command[C],
    instance: C,
    *,
    output: Output,
    state: State[Any],
    deps: DepTypes = None,
) -> tuple[Resolved[C], Sequence[Resolved[Any]]]:
    try:
        implicit_deps = resolve_implicit_deps(command, instance)
        fn: Callable[..., Any] = resolve_invoke_handler(parsed_command, implicit_deps)

        implicit_deps[Output] = output
        implicit_deps[Command] = parsed_command
        implicit_deps[State] = state
        implicit_deps[SelfType] = implicit_deps[cast(Hashable, parsed_command.cmd_cls)]

        global_deps = resolve_global_deps(deps, implicit_deps)

        fulfilled_deps: dict[Hashable, Any] = {**implicit_deps, **global_deps}
        resolved = fulfill_deps(fn, fulfilled_deps)
    except InvokeResolutionError as e:
        raise InvokeResolutionError(
            f"Failed to invoke {parsed_command.cmd_cls} due to resolution failure."
        ) from e

    return (resolved, tuple(global_deps.values()))


def resolve_global_deps(
    deps: DepTypes, implicit_deps: dict[Hashable, Any]
) -> dict[Hashable, Any]:
    result: dict[Hashable, Any] = {}

    if not deps:
        return result

    # Coerce the sequence variant of input into the mapping equivalent.
    if isinstance(deps, Sequence):
        deps = {d: Dep(d) for d in deps}

    for source_function, dep in deps.items():
        # Deps need to be fulfilled, whereas raw values are taken directly.
        if isinstance(dep, Dep):
            dep_callable = resolve_callable_reference(dep.callable)  # pyright: ignore
            value = fulfill_deps(dep_callable, implicit_deps)
        else:
            value = Resolved(source_function, result=dep)

        # We map back to the source dep, i.e. the key in the input mapping. This
        # translates to the raw function in the sequence input, or the source
        # dep being overridden in the dict input.
        source_dep: Dep[Any] = Dep(source_function)
        result[source_dep] = value

    return result


def resolve_invoke_handler(
    command: Command[C], implicit_deps: dict[Hashable, Any]
) -> Callable[..., C]:
    fn = command.invoke

    if not fn:
        command_type = cast(Hashable, command.cmd_cls)
        instance = implicit_deps.get(command_type)
        if callable(instance):
            return instance.__call__  # pyright: ignore

        raise InvokeResolutionError(
            f"Cannot call `invoke` for a command which does not have an invoke handler: {command.cmd_cls}."
        )

    return resolve_callable_reference(fn)


def resolve_callable_reference(fn: InvokeCallableSpec[C] | None) -> InvokeCallable[C]:
    if isinstance(fn, str):
        try:
            module_name, fn_name = fn.rsplit(".", 1)
        except ValueError:
            raise InvokeResolutionError(
                f"Invoke `{fn}` must be a fully qualified reference to a function in a module."
            )

        # Let this bubble upwards if the modules doesn't exist.
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as e:
            name = getattr(e, "name", None) or str(e)
            raise InvokeResolutionError(
                f"No module '{name}' when attempting to load '{fn}'."
            )

        if not hasattr(module, fn_name):
            raise InvokeResolutionError(
                f"Module {module} does not have a function `{fn_name}`."
            )

        fn = getattr(module, fn_name)

    if not callable(fn):
        raise InvokeResolutionError(f"`{fn}` does not reference a valid callable.")

    return cast(Callable[..., Any], fn)


def resolve_implicit_deps(command: Command[T], instance: T) -> dict[Hashable, Any]:
    key = cast(Hashable, instance.__class__)
    deps: dict[Hashable, Any] = {key: instance}

    for arg in command.arguments:
        if not isinstance(arg, Subcommand):
            # Args do not produce dependencies themselves.
            continue

        option_instance = getattr(instance, cast(str, arg.field_name))
        if option_instance is None:
            # None is a valid subcommand instance value, but it won't exist as a dependency
            # where an actual command has been selected.
            continue

        # This **should** always end up producing a value (type). In order to have produced
        # a subcommand instance value of a given type, it would need to exist in the options.
        option = next(  # pragma: no branch
            o for o in arg.options.values() if isinstance(option_instance, o.cmd_cls)
        )
        deps.update(resolve_implicit_deps(option, option_instance))

    return deps


def fulfill_deps(
    fn: Callable[..., C], fulfilled_deps: dict[Hashable, Any], allow_empty: bool = False
) -> Resolved[C]:
    args: list[Any] = []
    result: dict[str, Any] = {}

    try:
        callable_view = CallableView.from_callable(fn, include_extras=True)
    except NameError as e:  # pragma: no cover
        name = getattr(e, "name", None) or str(e)
        raise InvokeResolutionError(
            f"Could not collect resolve reference to {name} for `{getattr(fn, '__name__', '')}`"
        )
    except (ValueError, AttributeError):
        # ValueError is common amongst builtins. Perhaps TypeView ought to be handling this.
        # AttributeError is currently an issue with Enums, I think TypeView should **definitely**
        # handle this.
        return Resolved(fn, result)

    for index, param_view in enumerate(callable_view.parameters):
        type_view: TypeView[Any] = param_view.type_view  # pyright: ignore

        # "Native" supported annotations
        if type_view.is_annotated and SelfType in type_view.metadata:
            result[param_view.name] = fulfilled_deps[SelfType]

        elif type_view.fallback_origin in fulfilled_deps:
            result[param_view.name] = fulfilled_deps[type_view.fallback_origin]

        # "Dep(foo)" annotations
        elif deps := cast(List[Dep[Any]], find_annotations(type_view, Dep)):
            assert len(deps) == 1
            dep = deps[0]

            # Whereas everything else should be a resolvable explicit Dep, which might have either
            # already been fullfullfilled, or yet need to be.
            if dep not in fulfilled_deps:
                fulfilled_deps[dep] = fulfill_deps(
                    cast(Callable[..., Any], dep.callable), fulfilled_deps
                )

            result[param_view.name] = fulfilled_deps[dep]

        # Method `self` arguments can be assumed to be typed as the literal class they reside inside,
        # These classes should always be already fulfilled by the root command structure.
        elif index == 0 and inspect.ismethod(fn):
            cls = get_method_class(fn)

            if has_command(fn.__self__):
                value = fulfilled_deps[cls]
                args.append(value)

        # If there's a default, we can just skip it and let the default fulfill the value.
        # Alternatively, `allow_empty` might be True to indicate we shouldn't error.
        elif param_view.has_default or allow_empty:
            continue

        # Non-annotated args are either implicit dependencies (and thus already fulfilled),
        # or arguments that we cannot fulfill and should error.
        else:
            param_annotation = (
                param_view.type_view.repr_type
                if param_view.has_annotation
                else "<empty>"
            )

            raise InvokeResolutionError(
                f"`{param_view.name}: {param_annotation}` "
                f"is not a valid dependency for Dep({fn.__name__})."
            )

    return Resolved(fn, kwargs=result, args=tuple(args))
