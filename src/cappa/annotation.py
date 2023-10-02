from __future__ import annotations

import enum
import types
import typing

from typing_inspect import is_literal_type

from cappa.typing import T, backend_type, is_none_type, is_subclass, is_union_type

__all__ = [
    "parse_value",
    "parse_literal",
    "parse_list",
    "parse_set",
    "parse_union",
    "parse_tuple",
    "parse_none",
    "detect_choices",
]


type_priority: typing.Final = types.MappingProxyType(
    {
        None: 0,
        float: 1,
        int: 2,
        bool: 3,
        str: 4,
    }
)


def parse_value(annotation: type) -> typing.Callable:
    """Create a value parser for the given annotation.

    Examples:
        >>> from typing import List, Literal, Tuple
        >>> list_parser = parse_value(List[int])
        >>> tuple_parser = parse_value(Tuple[int, ...])
        >>> literal_parser = parse_literal(Literal["foo"])
    """
    origin = typing.get_origin(annotation) or annotation
    type_args = typing.get_args(annotation)

    if is_literal_type(origin):
        return parse_literal(*type_args)

    if is_union_type(origin):
        return parse_union(*type_args)

    if is_subclass(origin, (str, bool, int, float)):
        return origin

    if is_none_type(origin):
        return parse_none()

    if is_subclass(origin, list):
        return parse_list(*type_args)

    if is_subclass(origin, set):
        return parse_set(*type_args)

    if is_subclass(origin, tuple):
        return parse_tuple(*type_args)

    return origin


def parse_literal(type_arg: T) -> typing.Callable[[typing.Any], T]:
    """Create a value parser for a given literal value."""
    mapping_fn: typing.Type = type(type_arg)

    def literal_mapper(value):
        mapped_value = mapping_fn(value)
        if mapped_value == type_arg:
            return mapped_value

        raise ValueError(f"{value} != {type_arg}")

    return literal_mapper


def parse_list(of_type: type[T]) -> typing.Callable[[typing.Any], list[T]]:
    """Create a value parser for a list of given type `of_type`."""
    inner_mapper = parse_value(of_type)

    def list_mapper(value: list):
        return [inner_mapper(v) for v in value]

    return list_mapper


def parse_set(of_type: type[T]) -> typing.Callable[[typing.Any], set[T]]:
    """Create a value parser for a list of given type `of_type`."""
    inner_mapper = parse_value(of_type)

    def set_mapper(value: list):
        return {inner_mapper(v) for v in value}

    return set_mapper


def parse_tuple(*type_args: type) -> typing.Callable[[typing.Any], tuple]:
    """Create a value parser for a tuple with type-args of given `type_args`."""
    if len(type_args) == 2 and type_args[1] == ...:
        inner_type: type = type_args[0]
        list_mapper = parse_value(typing.List[inner_type])  # type: ignore

        def unbounded_tuple_mapper(value: list):
            return tuple(list_mapper(value))

        return unbounded_tuple_mapper

    def tuple_mapper(value: list):
        result = []
        for inner_type, inner_value in zip(type_args, value):
            inner_mapper = parse_value(inner_type)
            inner_value = inner_mapper(inner_value)
            result.append(inner_value)
        return tuple(result)

    return tuple_mapper


def parse_union(*type_args: type) -> typing.Callable[[typing.Any], typing.Any]:
    """Create a value parser for a Union with type-args of given `type_args`."""

    def type_priority_key(type_) -> int:
        return type_priority.get(type_, 0)

    mappers: list[typing.Callable] = [
        parse_value(t) for t in sorted(type_args, key=type_priority_key)
    ]

    def union_mapper(value):
        for mapper in mappers:
            try:
                return mapper(value)
            except ValueError:
                pass

        raise ValueError(
            f"Could not parse '{value}' given options: {', '.join(backend_type(t) for t in type_args)}"
        )

    return union_mapper


def parse_none():
    """Create a value parser for None."""

    def map_none(value):
        if value is None:
            return

        raise ValueError(value)

    return map_none


def detect_choices(origin: type, type_args: tuple[type, ...]) -> list[str] | None:
    if is_subclass(origin, enum.Enum):
        assert issubclass(origin, enum.Enum)
        return [v.value for v in origin]

    if is_subclass(origin, (tuple, list, set)):
        origin = typing.cast(type, type_args[0])
        type_args = typing.get_args(type_args[0])

    if is_union_type(origin):
        if all(is_literal_type(t) for t in type_args):
            return [str(typing.get_args(t)[0]) for t in type_args]

    return None
