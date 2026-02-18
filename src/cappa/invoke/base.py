from __future__ import annotations

import contextlib
import importlib
import inspect
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Generator,
    Hashable,
    List,
    Sequence,
    cast,
)

from typing_extensions import TypeGuard

from cappa.class_inspect import has_command
from cappa.command import Command
from cappa.invoke.types import (
    C,
    Dep,
    DepTypes,
    InvokeCallable,
    InvokeCallableSpec,
    InvokeResolutionError,
    Resolved,
    SelfType,
)
from cappa.output import Output
from cappa.state import State
from cappa.type_view import CallableView, TypeView
from cappa.typing import find_annotations, get_method_class


def resolve_callable(
    command: Command[Any],
    parsed_command: Command[C],
    instance: C,
    *,
    implicit_deps: dict[Hashable, Any],
    output: Output,
    state: State[Any],
    deps: DepTypes = None,
) -> tuple[Resolved[C], Sequence[Resolved[Any]]]:
    try:
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
        deps = {cast(InvokeCallable[Any], d): Dep(d) for d in deps}

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

        # Unwrap TypeAliasType instances like `type Foo = Annotated[int, Dep(foo)]`
        type_view = type_view.strip_type_alias()

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


def is_implicit_context_manager(
    value: Any,
) -> TypeGuard[Callable[..., Generator[Any, Any, Any]]]:
    return inspect.isgeneratorfunction(value)


def is_context_manager(value: Any) -> TypeGuard[contextlib.AbstractContextManager[Any]]:
    return isinstance(value, contextlib.AbstractContextManager)


def is_implicit_async_context_manager(
    value: Any,
) -> TypeGuard[Callable[..., AsyncGenerator[Any, Any]]]:
    return inspect.isasyncgenfunction(value)


def is_async_context_manager(
    value: Any,
) -> TypeGuard[contextlib.AbstractAsyncContextManager[Any]]:
    return isinstance(value, contextlib.AbstractAsyncContextManager)
