from __future__ import annotations

import functools
import types
import typing
from datetime import date, datetime, time

from cappa.file_io import FileMode
from cappa.type_view import TypeView
from cappa.typing import T

__all__ = [
    "parse_list",
    "parse_literal",
    "parse_none",
    "parse_set",
    "parse_tuple",
    "parse_union",
    "parse_value",
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
    def wrapper(annotation: T | TypeView[T]) -> T:
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

    if annotation.is_subclass_of((str, bool, int, float)):
        return annotation.annotation

    if annotation.is_none_type:
        return parse_none  # type: ignore

    if annotation.is_subclass_of(datetime):
        return datetime.fromisoformat  # type: ignore

    if annotation.is_subclass_of(date):
        return date.fromisoformat  # type: ignore

    if annotation.is_subclass_of(time):
        return time.fromisoformat  # type: ignore

    if annotation.is_subclass_of(list):
        return parse_list(annotation)  # pyright: ignore

    if annotation.is_subclass_of(set):
        return parse_set(annotation)  # pyright: ignore

    if annotation.is_subclass_of(tuple):
        return parse_tuple(annotation)  # pyright: ignore

    if annotation.is_subclass_of((typing.TextIO, typing.BinaryIO)):
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

        options = ", ".join(f"'{t}'" for t in annotation.args)
        raise ValueError(
            f"Invalid choice: '{value}' (choose from literal values {options})"
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

    def type_priority_key(type_type_view: TypeView) -> int:
        return type_priority.get(type_type_view.annotation, 1)

    mappers: list[tuple[TypeView[T], typing.Callable]] = [
        (t, parse_value(t))
        for t in sorted(annotation.inner_types, key=type_priority_key)
    ]

    def union_mapper(value):
        exceptions = []
        for mapper_type_view, mapper in mappers:
            try:
                return mapper(value)
            except (ValueError, TypeError) as e:
                if mapper is parse_none:
                    err = " - <no value>"
                else:
                    err = f" - {mapper_type_view.repr_type}: {e}"
                exceptions.append(err)

        # Perhaps we should be showing all failed mappings at some point. As-is,
        # the preferred interpretation will be determined by order in the event
        # of all mappings failing
        reasons = "\n".join(exceptions)
        raise ValueError(f"Possible variants\n{reasons}")

    return union_mapper


def parse_none(value: typing.Any) -> None:
    """Create a value parser for None.

    Default values are not run through Arg.parse, so there's no way to arrive at a `None` value.
    """
    raise ValueError(value)


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

            if annotation.is_subclass_of(typing.BinaryIO):
                file_mode.mode += "b"

        return file_mode(value)

    return file_io_mapper
