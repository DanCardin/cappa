from __future__ import annotations

import importlib
import inspect
import typing
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from typing_extensions import get_type_hints

from cappa.command import Command, HasCommand
from cappa.subcommand import Subcommands
from cappa.typing import find_type_annotation

T = typing.TypeVar("T", bound=HasCommand)


@dataclass(frozen=True)
class Dep(typing.Generic[T]):
    """Describes the callable required to fullfill a given dependency."""

    callable: Callable


def invoke_callable(
    command: Command,
    parsed_command: Command[T],
    instance: T,
    deps: typing.Sequence[Callable]
    | typing.Mapping[Callable, Dep | typing.Any]
    | None = None,
):
    fn: Callable = resolve_invoke_handler(parsed_command)
    implicit_deps = resolve_implicit_deps(command, instance)
    fullfilled_deps = resolve_global_deps(deps, implicit_deps)

    return fullfill_deps(fn, fullfilled_deps)


def resolve_global_deps(
    deps: typing.Sequence[Callable] | typing.Mapping[Callable, Dep | typing.Any] | None,
    implicit_deps: dict,
) -> dict:
    if not deps:
        return implicit_deps

    # Coerce the sequence variant of input into the mapping equivalent.
    if isinstance(deps, Sequence):
        deps = typing.cast(typing.Mapping, {d: Dep(d) for d in deps})

    for source_function, dep in deps.items():
        # Deps need to be fullfilled, whereas raw values are taken directly.
        if isinstance(dep, Dep):
            value = fullfill_deps(dep.callable, implicit_deps)
        else:
            value = dep

        # We map back to the source dep, i.e. the key in the input mapping. This
        # translates to the raw function in the sequence input, or the source
        # dep being overridden in the dict input.
        source_dep: Dep = Dep(source_function)
        implicit_deps[source_dep] = value

    return implicit_deps


def resolve_invoke_handler(command: Command) -> Callable:
    fn = command.invoke

    if not fn:
        raise ValueError(
            f"Cannot call `invoke` for a command which does not have an invoke handler: {command.cmd_cls}."
        )

    if isinstance(fn, str):
        try:
            module_name, fn_name = fn.rsplit(".", 1)
        except ValueError:
            raise ValueError(
                f"Invoke `{fn}` must be a fully qualified reference to a function in a module."
            )

        # Let this bubble upwards if the modules doesn't exist.
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as e:
            name = getattr(e, "name") or str(e)
            raise ValueError(f"No module '{name}' when attempting to load '{fn}'.")

        if not hasattr(module, fn_name):
            raise AttributeError(
                f"Module {module} does not have a function `{fn_name}`."
            )

        fn = getattr(module, fn_name)

    if not callable(fn):
        raise ValueError(f"`{fn}` does not reference a valid callable.")

    return fn


def resolve_implicit_deps(command: Command, instance: HasCommand) -> dict:
    deps = {instance.__class__: instance}

    for arg in command.arguments:
        if not isinstance(arg, Subcommands):
            # Args do not produce dependencies themselves.
            continue

        option_instance = getattr(instance, arg.name)
        if option_instance is None:
            # None is a valid subcommand instance value, but it wont exist as a dependency
            # where an actual command has been selected.
            continue

        # This **should** always end up producing a value (type). In order to have produced
        # a subcommand instance value of a given type, it would need to exist in the options.
        option = next(  # pragma: no branch
            o for o in arg.options.values() if isinstance(option_instance, o.cmd_cls)
        )
        deps.update(resolve_implicit_deps(option, option_instance))

    return deps


def fullfill_deps(fn: Callable, fullfilled_deps: dict) -> typing.Any:
    result = {}

    signature = inspect.signature(fn)
    try:
        annotations = get_type_hints(fn, include_extras=True)
    except NameError as e:  # pragma: no cover
        name = getattr(e, "name") or str(e)
        raise NameError(
            f"Could not collect resolve reference to {name} for Dep({fn.__name__})"
        )

    for name, param in signature.parameters.items():
        annotation = annotations.get(name)

        if annotation is None:
            dep = None
        else:
            dep, annotation = find_type_annotation(annotation, Dep)

        if dep is None:
            # Non-annotated args are either implicit dependencies (and thus already fullfilled),
            # or arguments that we cannot fullfill
            if annotation not in fullfilled_deps:
                if param.default is param.empty:
                    annotation_name = annotation.__name__ if annotation else "<empty>"
                    raise RuntimeError(
                        f"`{name}: {annotation_name}` is not a valid dependency for Dep({fn.__name__})."
                    )

                # if there's a default, we can just skip it and let the default fullfill the value.
                continue

            value = fullfilled_deps[annotation]

        else:
            # Whereas everything else should be a resolvable explicit Dep, which might have either
            # already been fullfullfilled, or yet need to be.
            if dep in fullfilled_deps:
                value = fullfilled_deps[dep]
            else:
                value = fullfill_deps(dep.callable, fullfilled_deps)
                fullfilled_deps[dep] = value

        result[name] = value

    return fn(**result)
