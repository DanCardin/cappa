from __future__ import annotations

import sys
import types
import typing

import typing_inspect
from typing_extensions import Annotated
from typing_inspect import is_literal_type, typing_extensions

if sys.version_info < (3, 10):
    NoneType = type(None)  # pragma: no cover
else:
    NoneType = types.NoneType  # type: ignore

T = typing.TypeVar("T")

missing = ...
MISSING: typing.TypeAlias = type(missing)  # type: ignore


def find_type_annotation(
    type_hint: typing.Type, kind: typing.Type[T]
) -> tuple[T | None, typing.Type]:
    instance = None

    if typing_extensions.get_origin(type_hint) is Annotated:
        annotations = type_hint.__metadata__
        type_hint = type_hint.__origin__

        for annotation in annotations:
            if isinstance(annotation, kind):
                instance = annotation
                break

            if isinstance(annotation, type) and issubclass(annotation, kind):
                instance = annotation()
                break

    return instance, type_hint


def assert_not_missing(value: T | MISSING) -> T:
    assert not isinstance(value, MISSING), value
    return typing.cast(T, value)


def assert_type(value: typing.Any, typ: type[T]) -> T:
    assert isinstance(value, typ), value
    return typing.cast(T, value)


def backend_type(typ) -> str:
    if is_literal_type(typ):
        return typing.get_args(typ)[0]

    return f"<{typ.__name__}>"


def is_union_type(typ):
    if typing_inspect.is_union_type(typ):
        return True

    if hasattr(types, "UnionType") and typ is types.UnionType:
        return True  # pragma: no cover
    return False


def is_none_type(typ):
    return typ is NoneType


def is_subclass(typ, superclass):
    if not isinstance(typ, type):
        return False

    if typ is str:
        return False

    return issubclass(typ, superclass)
