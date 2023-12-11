from __future__ import annotations

import sys
import types
import typing
from dataclasses import dataclass
from inspect import cleandoc

import typing_extensions
import typing_inspect
from typing_extensions import Annotated, get_args, get_origin
from typing_inspect import is_literal_type

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

    if get_origin(type_hint) is Annotated:
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
            typing_extensions.assert_never(doc_type)  # type: ignore

    return ObjectAnnotation(obj=instance, annotation=type_hint, doc=doc)


def assert_type(value: typing.Any, typ: type[T]) -> T:
    assert isinstance(value, typ), value
    return typing.cast(T, value)


def backend_type(typ) -> str:
    if is_literal_type(typ):
        return get_args(typ)[0]

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


def get_type_hints(obj, include_extras=False):
    result = typing_extensions.get_type_hints(obj, include_extras=include_extras)
    if sys.version_info < (3, 11):  # pragma: no cover
        return fix_annotated_optional_type_hints(result)
    return result


def fix_annotated_optional_type_hints(
    hints: dict[str, typing.Any]
) -> dict[str, typing.Any]:  # pragma: no cover
    """Normalize `Annotated` interacting with `get_type_hints` in versions <3.11.

    https://github.com/python/cpython/issues/90353.
    """
    for param_name, hint in hints.items():
        args = get_args(hint)
        if (
            get_origin(hint) is typing.Union
            and get_origin(next(iter(args))) is Annotated
        ):
            hints[param_name] = next(iter(args))
    return hints
