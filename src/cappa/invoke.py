from __future__ import annotations

import importlib
import typing
from dataclasses import dataclass

from typing_extensions import Callable, get_type_hints  # type: ignore

from cappa.command import Command, HasCommand
from cappa.typing import find_type_annotation

T = typing.TypeVar("T", bound=HasCommand)


@dataclass(frozen=True)
class Dep(typing.Generic[T]):
    callable: Callable[..., T]


def invoke(command: Command[T], instance: T):
    fn: Callable = resolve_invoke_handler(command)
    implicit_deps = resolve_implicit_deps(instance)
    kwargs = fullfill_deps(command, fn, implicit_deps)
    return fn(**kwargs)


def resolve_invoke_handler(command: Command) -> Callable:
    fn = command.invoke
    if not fn:
        raise ValueError(
            "Cannot call `invoke` for a command which does not have an invoke handler."
        )

    if isinstance(fn, str):
        try:
            module_name, fn_name = fn.rsplit(".", 1)
        except ValueError:
            raise ValueError(
                f"Invoke `{fn}` must be a fully qualified reference to a function in a module."
            )

        # Let this bubble upwards if the modules doesn't exist.
        module = importlib.import_module(module_name)

        if not hasattr(module, fn_name):
            raise AttributeError(
                f"Module '{module}' does not have a function {fn_name}"
            )

        fn = getattr(module, fn_name)
        if not callable(fn):
            raise ValueError(
                f"`{fn}` does not reference a valid callable 'invoke' handler."
            )

        return fn

    if callable(fn):
        return fn

    raise ValueError(f"`{fn}` is not a valid 'invoke' handler")


def resolve_implicit_deps(
    instance: HasCommand,
) -> dict[typing.Type[HasCommand], HasCommand]:
    deps = {instance.__class__: instance}
    for attr in instance.__dict__.values():
        if hasattr(attr, "__cappa__"):
            cls = attr.__class__
            deps[cls] = attr

            deps.update(resolve_implicit_deps(attr))

    return deps


def fullfill_deps(
    command: Command[T],
    fn: Callable,
    implicit_deps: dict[typing.Type[HasCommand], HasCommand],
    fullfilled_deps: dict[Dep, typing.Any] | None = None,
) -> dict[str, typing.Any]:
    if fullfilled_deps is None:
        fullfilled_deps = {}

    result = {}

    args = get_type_hints(fn)
    for name, annotation in args.items():
        dep, annotation = find_type_annotation(annotation, Dep)

        # non-annotated args are either implicit dependencies or arguments that we cannot fullfill
        if dep is None:
            value = collect_implicit_dep(implicit_deps, annotation)

        else:
            if dep in fullfilled_deps:
                continue

            value = collect_explicit_dep(annotation)

            fullfilled_deps[dep] = value

        result[name] = value

    return result


def collect_implicit_dep(
    implicit_deps: dict[typing.Type[HasCommand], HasCommand],
    annotation: typing.Type[HasCommand],
) -> HasCommand:
    if annotation not in implicit_deps:
        raise ValueError(f"{annotation} is not a valid dependency.")

    return implicit_deps[annotation]


def collect_explicit_dep(fn: Callable):
    return {}


def unpack(instance, *fields: str):
    ...
