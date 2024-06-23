from __future__ import annotations

import contextlib
import importlib
import inspect
import typing
from collections.abc import Callable
from dataclasses import dataclass, field

from cappa.command import Command, HasCommand
from cappa.output import Exit, Output
from cappa.subcommand import Subcommand
from cappa.typing import find_type_annotation, get_type_hints

C = typing.TypeVar("C", bound=HasCommand)


class InvokeResolutionError(RuntimeError):
    """Raised for errors encountered during evaluation of invoke dependencies."""


@dataclass(frozen=True)
class Dep(typing.Generic[C]):
    """Describes the callable required to fulfill a given dependency."""

    callable: Callable


@dataclass
class Resolved(typing.Generic[C]):
    callable: Callable[..., C]
    kwargs: dict[str, typing.Any | Resolved] = field(default_factory=dict)
    result: typing.Any = ...
    is_resolved: bool = False

    @contextlib.contextmanager
    def get(self, output: Output) -> typing.Generator[typing.Any, None, None]:
        """Get the resolved value.

        The value itself is cached in the event it's used as a dependency to more
        than one dependency.
        """
        if self.is_resolved:
            yield self.result
            return

        with contextlib.ExitStack() as stack:
            # Non-resolved values are literal values that can be recorded directly.
            finalized_kwargs = dict(self.iter_kwargs(is_resolved=False))

            # Resolved values need to be recursed into. In order to handle the
            # wrapping context manager, we need to enter all contexts, and only
            # exit at the end.
            for k, v in self.iter_kwargs(is_resolved=True):
                finalized_kwargs[k] = stack.enter_context(v.get(output))

            with self.handle_exit(output):
                callable: Callable = self.callable
                requires_management = inspect.isgeneratorfunction(callable)
                if requires_management:
                    # Yield functions are assumed to be context-maneger style generators
                    # what we just need to wrap...
                    callable = contextlib.contextmanager(callable)

                result = callable(**finalized_kwargs)
                is_context_manager = isinstance(
                    result, contextlib.AbstractContextManager
                )

                # And then enter before producing the result.
                if requires_management or is_context_manager:
                    result = stack.enter_context(result)

            self.result = result
            self.is_resolved = True
            yield result

    @contextlib.asynccontextmanager
    async def get_async(
        self, output: Output
    ) -> typing.AsyncGenerator[typing.Any, None]:
        """Get the resolved value, in an async context.

        Note, this is the exact same process as in `get`, except with `await`,
        `enter_async_context` and `async with`. There seems to be no way to
        share the logic between the two methods, so they just need to be kept
        in sync :shrug:.
        """
        if self.is_resolved:
            yield self.result
            return

        async with contextlib.AsyncExitStack() as stack:
            finalized_kwargs = dict(self.iter_kwargs(is_resolved=False))
            for k, v in self.iter_kwargs(is_resolved=True):
                finalized_kwargs[k] = await stack.enter_async_context(
                    v.get_async(output)
                )

            with self.handle_exit(output):
                callable: Callable = self.callable
                requires_management = inspect.isasyncgenfunction(callable)
                if requires_management:
                    callable = contextlib.asynccontextmanager(callable)

                result = callable(**finalized_kwargs)
                is_context_manager = isinstance(
                    result, contextlib.AbstractAsyncContextManager
                )

                if requires_management or is_context_manager:
                    result = await stack.enter_async_context(result)
                elif isinstance(result, typing.Coroutine):
                    result = await result

            self.result = result
            self.is_resolved = True
            yield result

    def iter_kwargs(self, *, is_resolved):
        for k, v in self.kwargs.items():
            if is_resolved == isinstance(v, self.__class__):
                yield k, v

    @classmethod
    @contextlib.contextmanager
    def handle_exit(cls, output: Output):
        try:
            yield
        except Exit as e:
            output.exit(e)
            raise e


def resolve_callable(
    command: Command,
    parsed_command: Command[C],
    instance: C,
    *,
    output: Output,
    deps: typing.Sequence[Callable]
    | typing.Mapping[Callable, Dep | typing.Any]
    | None = None,
) -> tuple[Resolved[C], typing.Sequence[Resolved]]:
    try:
        implicit_deps = resolve_implicit_deps(command, instance)
        fn: Callable = resolve_invoke_handler(parsed_command, implicit_deps)

        implicit_deps[Output] = output
        implicit_deps[Command] = parsed_command

        global_deps = resolve_global_deps(deps, implicit_deps)

        fulfilled_deps = {**implicit_deps, **global_deps}
        kwargs = fulfill_deps(fn, fulfilled_deps)
    except InvokeResolutionError as e:
        raise InvokeResolutionError(
            f"Failed to invoke {parsed_command.cmd_cls} due to resolution failure."
        ) from e

    return (Resolved(fn, kwargs), tuple(global_deps.values()))


def resolve_global_deps(
    deps: typing.Sequence[Callable] | typing.Mapping[Callable, Dep | typing.Any] | None,
    implicit_deps: dict,
) -> dict:
    result: dict[Dep, typing.Any] = {}

    if not deps:
        return result

    # Coerce the sequence variant of input into the mapping equivalent.
    if isinstance(deps, typing.Sequence):
        deps = typing.cast(typing.Mapping, {d: Dep(d) for d in deps})

    for source_function, dep in deps.items():
        # Deps need to be fulfilled, whereas raw values are taken directly.
        if isinstance(dep, Dep):
            value = Resolved(dep.callable, fulfill_deps(dep.callable, implicit_deps))
        else:
            value = Resolved(source_function, result=dep, is_resolved=True)

        # We map back to the source dep, i.e. the key in the input mapping. This
        # translates to the raw function in the sequence input, or the source
        # dep being overridden in the dict input.
        source_dep: Dep = Dep(source_function)
        result[source_dep] = value

    return result


def resolve_invoke_handler(
    command: Command[C], implicit_deps: dict
) -> Callable[..., C]:
    fn = command.invoke

    if not fn:
        command_type = command.cmd_cls
        instance = implicit_deps.get(command_type)
        if callable(instance):
            return instance.__call__

        raise InvokeResolutionError(
            f"Cannot call `invoke` for a command which does not have an invoke handler: {command.cmd_cls}."
        )

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
            name = getattr(e, "name") or str(e)
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

    return fn


def resolve_implicit_deps(command: Command, instance: HasCommand) -> dict:
    deps = {instance.__class__: instance}

    for arg in command.arguments:
        if not isinstance(arg, Subcommand):
            # Args do not produce dependencies themselves.
            continue

        option_instance = getattr(instance, arg.field_name)
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


def fulfill_deps(fn: Callable, fulfilled_deps: dict) -> typing.Any:
    result = {}

    signature = getattr(fn, "__signature__", None) or inspect.signature(fn)
    try:
        annotations = get_type_hints(fn, include_extras=True)
    except NameError as e:  # pragma: no cover
        name = getattr(e, "name") or str(e)
        raise InvokeResolutionError(
            f"Could not collect resolve reference to {name} for Dep({fn.__name__})"
        )

    for name, param in signature.parameters.items():
        annotation = annotations.get(name)

        if annotation is None:
            dep = None
        else:
            object_annotation = find_type_annotation(annotation, Dep)
            annotation = object_annotation.annotation
            objs = object_annotation.obj
            dep = objs[0] if objs else None

        annotation = typing.get_origin(annotation) or annotation

        if dep is None:
            # Non-annotated args are either implicit dependencies (and thus already fulfilled),
            # or arguments that we cannot fulfill
            if annotation not in fulfilled_deps:
                if param.default is param.empty:
                    annotation_name = annotation.__name__ if annotation else "<empty>"
                    raise InvokeResolutionError(
                        f"`{name}: {annotation_name}` is not a valid dependency for Dep({fn.__name__})."
                    )

                # if there's a default, we can just skip it and let the default fulfill the value.
                continue

            value = fulfilled_deps[annotation]

        else:
            # Whereas everything else should be a resolvable explicit Dep, which might have either
            # already been fullfullfilled, or yet need to be.
            if dep in fulfilled_deps:
                value = fulfilled_deps[dep]
            else:
                value = Resolved(
                    dep.callable, fulfill_deps(dep.callable, fulfilled_deps)
                )
                fulfilled_deps[dep] = value

        result[name] = value

    return result
