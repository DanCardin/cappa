from __future__ import annotations

import enum
import inspect
import typing
from dataclasses import dataclass

from typing_extensions import assert_never

from cappa.type_view import TypeView

try:
    from typing_extensions import Doc

    doc_type: type = Doc
except ImportError:  # pragma: no cover

    @dataclass
    class Doc:  # type: ignore
        documentation: str


__all__ = [
    "T",
    "assert_never",
    "assert_type",
    "detect_choices",
    "find_annotations",
]


T = typing.TypeVar("T")


def find_annotations(type_view: TypeView, kind: type[T]) -> list[T]:
    result = []
    for annotation in type_view.metadata:
        if isinstance(annotation, kind):
            result.append(annotation)

        if isinstance(annotation, type) and issubclass(annotation, kind):
            result.append(annotation())

    return result


def assert_type(value: typing.Any, typ: type[T]) -> T:
    assert isinstance(value, typ), value
    return typing.cast(T, value)


def detect_choices(type_view: TypeView) -> list[str] | None:
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


def get_method_class(fn):
    return inspect._findclass(fn)  # type: ignore
