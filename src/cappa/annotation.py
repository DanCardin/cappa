from __future__ import annotations

import enum
import types
import typing
from datetime import date, datetime, time

from typing_inspect import get_origin, is_literal_type

from cappa.file_io import FileMode
from cappa.typing import T, is_none_type, is_subclass, is_union_type

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
        ...: 1,
        float: 2,
        int: 3,
        bool: 4,
        str: 5,
    }
)


def parse_value(
    annotation: type, extra_annotations: typing.Iterable[type] = ()
) -> typing.Callable:
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

    if is_subclass(origin, datetime):
        return datetime.fromisoformat

    if is_subclass(origin, date):
        return date.fromisoformat

    if is_subclass(origin, time):
        return time.fromisoformat

    if is_none_type(origin):
        return parse_none

    if is_subclass(origin, list):
        return parse_list(*type_args)

    if is_subclass(origin, set):
        return parse_set(*type_args)

    if is_subclass(origin, tuple):
        return parse_tuple(*type_args)

    if is_subclass(origin, (typing.TextIO, typing.BinaryIO)):
        return parse_file_io(origin, extra_annotations)

    return origin


def parse_literal(*type_args: T) -> typing.Callable[[typing.Any], T]:
    """Create a value parser for a given literal value."""
    unique_type_args = set(type_args)

    def literal_mapper(value):
        if value in unique_type_args:
            return value

        for type_arg in unique_type_args:
            raw_value = str(type_arg)
            if raw_value == value:
                return type_arg

        options = ", ".join(f"'{t}'" for t in type_args)
        raise ValueError(
            f"Invalid choice: '{value}' (choose from literal values {options})"
        )

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
        return type_priority.get(type_, 1)

    mappers: list[tuple[type, typing.Callable]] = [
        (t, parse_value(t)) for t in sorted(type_args, key=type_priority_key)
    ]

    def union_mapper(value):
        exceptions = []
        for type_arg, mapper in mappers:
            try:
                return mapper(value)
            except (ValueError, TypeError) as e:
                if mapper is parse_none:
                    err = " - <no value>"
                else:
                    err = f" - {repr_type(type_arg)}: {e}"
                exceptions.append(err)

        # Perhaps we should be showing all failed mappings at some point. As-is,
        # the preferred interpretation will be determined by order in the event
        # of all mappings failing
        reasons = "\n".join(exceptions)
        raise ValueError(f"Possible variants\n{reasons}")

    return union_mapper


def parse_optional(
    parser: typing.Callable[[typing.Any | None], T],
) -> typing.Callable[[typing.Any | None], T | None]:
    def optional_mapper(value) -> T | None:
        if value is None:
            return None

        return parser(value)

    return optional_mapper


def parse_none(value):
    """Create a value parser for None."""
    if value is None:
        return

    raise ValueError(value)


def parse_file_io(
    annotation: type, extra_annotations: typing.Iterable[type]
) -> typing.Callable:
    def file_io_mapper(value: str):
        try:
            file_mode: FileMode = next(
                typing.cast(FileMode, f)
                for f in extra_annotations
                if isinstance(f, FileMode)
            )
        except StopIteration:
            file_mode = FileMode()

            if issubclass(annotation, typing.BinaryIO):
                file_mode.mode += "b"

        return file_mode(value)

    return file_io_mapper


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

    if is_literal_type(origin):
        return [str(t) for t in type_args]

    return None


def is_sequence_type(typ):
    return is_subclass(get_origin(typ) or typ, (typing.List, typing.Tuple, typing.Set))


def repr_type(t):
    if isinstance(t, type) and not typing.get_origin(t):
        return str(t.__name__)

    return str(t).replace("typing.", "")
