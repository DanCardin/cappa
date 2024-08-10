from __future__ import annotations

import enum
import types
import typing

from typing_inspect import get_origin, is_literal_type, is_optional_type

from cappa.typing import get_optional_type, is_subclass, is_union_type

__all__ = [
    "detect_choices",
]


type_priority: typing.Final = types.MappingProxyType(
    {
        None: 0,
        ...: 1,
        float: 2,
        int: 3,
        bool: 4,
        str: 5,
    }
)


def detect_choices(annotation: type) -> list[str] | None:
    if is_optional_type(annotation):
        annotation = get_optional_type(annotation)

    origin = typing.get_origin(annotation) or annotation
    type_args = typing.get_args(annotation)
    if is_subclass(origin, enum.Enum):
        return [v.value for v in origin]  # type: ignore

    if is_subclass(origin, (tuple, list, set)):
        origin = typing.cast(type, type_args[0])
        type_args = typing.get_args(type_args[0])

    if is_union_type(origin):
        if all(is_literal_type(t) for t in type_args):
            return [str(typing.get_args(t)[0]) for t in type_args]

    if is_literal_type(origin):
        return [str(t) for t in type_args]

    return None


def is_sequence_type(typ):
    return is_subclass(get_origin(typ) or typ, (typing.List, typing.Tuple, typing.Set))


def repr_type(t):
    if isinstance(t, type) and not typing.get_origin(t):
        return str(t.__name__)

    return str(t).replace("typing.", "")
