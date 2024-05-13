from __future__ import annotations

import enum
import typing
from dataclasses import dataclass

from type_lens import TypeView

try:
    from typing_extensions import Doc

    doc_type: type = Doc
except ImportError:  # pragma: no cover

    @dataclass
    class Doc:  # type: ignore
        documentation: str


T = typing.TypeVar("T")

missing = ...
MISSING: typing.TypeAlias = type(missing)  # type: ignore


def find_annotations(type_view: TypeView, kind: type[T]) -> list[T]:
    if kind is None:
        return []

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

    # origin = typing.get_origin(annotation) or annotation
    # type_args = typing.get_args(annotation)
    if type_view.is_subclass_of(enum.Enum):
        return [v.value for v in type_view.annotation]

    if type_view.is_subclass_of((tuple, list, set)):
        type_view = type_view.inner_types[0]

    if type_view.is_union:
        if all(t.is_literal for t in type_view.inner_types):
            print(type_view.inner_types)
            return [str(t.args[0]) for t in type_view.inner_types]

    if type_view.is_literal:
        return [str(t) for t in type_view.args]

    return None
