from __future__ import annotations

import enum
import inspect
import sys
import typing
from dataclasses import dataclass
from types import MethodType
from typing import Any, Protocol, TypeVar

import typing_extensions
from typing_extensions import assert_never

from cappa.type_view import TypeView


class DocType(Protocol):
    documentation: str


try:
    from typing_extensions import Doc as TypingExtensionsDoc

    Doc: type[DocType] = TypingExtensionsDoc
except ImportError:  # pragma: no cover

    @dataclass
    class InternalDoc:
        documentation: str

    Doc = InternalDoc


__all__ = [
    "Doc",
    "T",
    "assert_never",
    "assert_type",
    "detect_choices",
    "find_annotations",
]


T = TypeVar("T")


def find_annotations(type_view: TypeView[Any], kind: type[T]) -> list[T]:
    result: list[T] = []
    for annotation in type_view.metadata:
        if isinstance(annotation, kind):
            result.append(annotation)

        if isinstance(annotation, type) and issubclass(annotation, kind):
            result.append(annotation())

    return result


def assert_type(value: Any, typ: type[T]) -> T:
    assert isinstance(value, typ), value
    return value


def detect_choices(type_view: TypeView[Any]) -> list[str] | None:
    if type_view.is_optional:
        type_view = type_view.strip_optional()

    if type_view.is_subclass_of(enum.Enum):
        return [v.value for v in type_view.annotation]

    if type_view.is_subclass_of((list, set)) or type_view.is_variadic_tuple:
        type_view = type_view.inner_types[0]

    if type_view.is_union:
        if all(t.is_literal for t in type_view.inner_types):
            return [str(t.args[0]) for t in type_view.inner_types]

    if type_view.is_literal:
        return [str(t) for t in type_view.args]

    return None


def get_method_class(fn: MethodType) -> type:
    return inspect._findclass(fn)  # type: ignore


if sys.version_info < (3, 12):

    def is_type_alias(type_view: TypeView[Any]) -> bool:
        type_alias_type = (
            typing_extensions.TypeAliasType
            if hasattr(typing_extensions, "TypeAliasType")
            else None
        )
        if type_alias_type:
            return isinstance(type_view.annotation, type_alias_type)
        return False

else:

    def is_type_alias(type_view: TypeView[Any]) -> bool:
        backport_type_alias_type = (
            typing_extensions.TypeAliasType
            if hasattr(typing_extensions, "TypeAliasType")
            else None
        )
        type_alias_types = tuple(
            t for t in (typing.TypeAliasType, backport_type_alias_type) if t is not None
        )
        return isinstance(type_view.annotation, type_alias_types)
