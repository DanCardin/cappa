from __future__ import annotations

import sys
import types
import typing
from dataclasses import dataclass
from inspect import cleandoc

import typing_inspect
from typing_extensions import Annotated, assert_never
from typing_inspect import is_literal_type, typing_extensions

try:
    from typing_extensions import Doc  # type: ignore

    doc_type: type | None = Doc
except ImportError:  # pragma: no cover
    doc_type = None

if sys.version_info < (3, 10):
    NoneType = type(None)  # pragma: no cover
else:
    NoneType = types.NoneType  # type: ignore

T = typing.TypeVar("T")

missing = ...
MISSING: typing.TypeAlias = type(missing)  # type: ignore


@dataclass
class ObjectAnnotation(typing.Generic[T]):
    obj: T | None
    annotation: typing.Type
    doc: str | None = None


def find_type_annotation(
    type_hint: typing.Type, kind: typing.Type[T]
) -> ObjectAnnotation[T]:
    instance = None
    doc = None

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

        if doc_type:
            for annotation in annotations:
                if isinstance(annotation, doc_type):
                    doc = cleandoc(annotation.documentation)  # type: ignore
                    break
        else:
            assert_never(doc_type)  # type: ignore

    return ObjectAnnotation(obj=instance, annotation=type_hint, doc=doc)


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
