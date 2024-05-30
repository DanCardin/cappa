from __future__ import annotations

import functools
import types
import typing

from type_lens import TypeView

from cappa.file_io import FileMode
from cappa.typing import T, backend_type

__all__ = [
    "parse_value",
    "parse_literal",
    "parse_list",
    "parse_set",
    "parse_union",
    "parse_tuple",
    "parse_none",
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


def wrap_type_view(fn):
    @functools.wraps(fn)
    def wrapper(annotation: T | TypeView[T]):
        if not isinstance(annotation, TypeView):
            annotation = TypeView(annotation)
        return fn(annotation)

    return wrapper


@wrap_type_view
def parse_value(annotation: TypeView[T]) -> typing.Callable[[typing.Any], T]:
    """Create a value parser for the given annotation.

    Examples:
        >>> from typing import List, Literal, Tuple
        >>> list_parser = parse_value(List[int])
        >>> tuple_parser = parse_value(Tuple[int, ...])
        >>> literal_parser = parse_literal(Literal["foo"])
    """
    if annotation.is_literal:
        return parse_literal(annotation)

    if annotation.is_union:
        return parse_union(annotation)

    if annotation.is_subtype_of((str, bool, int, float)):
        return annotation.annotation

    if annotation.is_none_type:
        return parse_none(annotation)

    if annotation.is_subtype_of(list):
        return parse_list(annotation)

    if annotation.is_subtype_of(set):
        return parse_set(annotation)

    if annotation.is_subtype_of(tuple):
        return parse_tuple(annotation)

    if annotation.is_subtype_of((typing.TextIO, typing.BinaryIO)):
        return parse_file_io(annotation)

    return annotation.annotation


@wrap_type_view
def parse_literal(annotation: TypeView[T]) -> typing.Callable[[typing.Any], T]:
    """Create a value parser for a given literal value."""
    unique_type_args = set(annotation.args)

    def literal_mapper(value):
        if value in unique_type_args:
            return value

        for type_arg in unique_type_args:
            raw_value = str(type_arg)
            if raw_value == value:
                return type_arg

        raise ValueError(
            f"Invalid choice: '{value}' (choose from {', '.join(str(t) for t in annotation.args)})"
        )

    return literal_mapper


@wrap_type_view
def parse_list(annotation: TypeView[list[T]]) -> typing.Callable[[typing.Any], list[T]]:
    """Create a value parser for a list of given type `of_type`."""
    inner_mapper = parse_value(annotation.inner_types[0])

    def list_mapper(value: list[typing.Any]) -> list[T]:
        return [inner_mapper(v) for v in value]

    return list_mapper


@wrap_type_view
def parse_set(annotation: TypeView[list[T]]) -> typing.Callable[[typing.Any], set[T]]:
    """Create a value parser for a list of given type `of_type`."""
    inner_mapper = parse_value(annotation.inner_types[0])

    def set_mapper(value: list[typing.Any]) -> set[T]:
        return {inner_mapper(v) for v in value}

    return set_mapper


@wrap_type_view
def parse_tuple(annotation: TypeView[T]) -> typing.Callable[[typing.Any], tuple[T]]:
    """Create a value parser for a tuple with type-args of given `type_args`."""
    if annotation.is_variadic_tuple:
        assert annotation.args
        inner_type = annotation.args[0]
        list_mapper = parse_list(typing.List[inner_type])  # type: ignore

        def unbounded_tuple_mapper(value: list):
            return tuple(list_mapper(value))

        return unbounded_tuple_mapper

    def tuple_mapper(value: list):
        result = []
        for inner_type, inner_value in zip(annotation.inner_types, value):
            inner_mapper = parse_value(inner_type)
            inner_value = inner_mapper(inner_value)
            result.append(inner_value)
        return tuple(result)

    return tuple_mapper


@wrap_type_view
def parse_union(annotation: TypeView[T]) -> typing.Callable[[typing.Any], T]:
    """Create a value parser for a Union with type-args of given `type_args`."""

    def type_priority_key(type_) -> int:
        return type_priority.get(type_, 1)

    mappers: list[typing.Callable] = [
        parse_value(t) for t in sorted(annotation.args, key=type_priority_key)
    ]

    def union_mapper(value):
        for mapper in mappers:
            try:
                return mapper(value)
            except (ValueError, TypeError):
                pass

        raise ValueError(
            f"Could not parse '{value}' given options: {', '.join(backend_type(t) for t in annotation.inner_types)}"
        )

    return union_mapper


def parse_optional(
    parser: typing.Callable[[typing.Any | None], T],
) -> typing.Callable[[typing.Any | None], T | None]:
    def optional_mapper(value) -> T | None:
        if value is None:
            return None

        return parser(value)

    return optional_mapper


@wrap_type_view
def parse_none(_: TypeView[None]) -> typing.Callable[[typing.Any], None]:
    """Create a value parser for None."""

    def map_none(value: typing.Any) -> None:
        if value is None:
            return

        raise ValueError(value)

    return map_none


@wrap_type_view
def parse_file_io(annotation: TypeView) -> typing.Callable:
    def file_io_mapper(value: str):
        try:
            file_mode: FileMode = next(
                typing.cast(FileMode, f)
                for f in annotation.metadata
                if isinstance(f, FileMode)
            )
        except StopIteration:
            file_mode = FileMode()

            if annotation.is_subtype_of(typing.BinaryIO):
                file_mode.mode += "b"

        return file_mode(value)

    return file_io_mapper
