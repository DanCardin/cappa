from __future__ import annotations

import importlib
import inspect
import typing
from collections.abc import Callable
from dataclasses import dataclass

from typing_extensions import get_type_hints

from cappa.command import Command, HasCommand
from cappa.typing import find_type_annotation

T = typing.TypeVar("T", bound=HasCommand)


@dataclass(frozen=True)
class Dep(typing.Generic[T]):
    """Describes the callable required to fullfill a given dependency."""

    callable: Callable[..., T]


def invoke_callable(command: Command[T], instance: T):
    fn: Callable = resolve_invoke_handler(command)
    implicit_deps = resolve_implicit_deps(instance)
    return fullfill_deps(fn, implicit_deps)


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
        module = importlib.import_module(module_name)

        if not hasattr(module, fn_name):
            raise AttributeError(
                f"Module {module} does not have a function `{fn_name}`"
            )

        fn = getattr(module, fn_name)

    if not callable(fn):
        raise ValueError(f"`{fn}` does not reference a valid callable.")

    return fn


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


def fullfill_deps(fn: Callable, fullfilled_deps: dict) -> typing.Any:
    result = {}

    signature = inspect.signature(fn)
    annotations = get_type_hints(fn, include_extras=True)

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
                        f"`{name}: {annotation_name}` is not a valid dependency."
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
