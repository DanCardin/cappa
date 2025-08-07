from __future__ import annotations

import enum
import functools
import types
from datetime import date, datetime, time
from typing import (
    Any,
    BinaryIO,
    Callable,
    Final,
    List,
    Sequence,
    TextIO,
    Type,
    Union,
    cast,
)

from typing_extensions import Never

from cappa.file_io import FileMode
from cappa.state import S, State
from cappa.type_view import TypeView
from cappa.typing import T

__all__ = [
    "parse_list",
    "parse_literal",
    "parse_set",
    "parse_tuple",
    "parse_union",
    "parse_value",
    "unpack_arguments",
]


type_priority: Final = types.MappingProxyType(
    {
        None: 0,
        ...: 1,
        float: 2,
        int: 3,
        bool: 4,
        str: 5,
    }
)

Parser = Callable[..., T]
MaybeTypeView = Union[Type[T], TypeView[Type[T]]]


def unpack_arguments(value: object, type_view: TypeView[T]) -> Parser[T]:
    """`parse=` compatible function that splats values into a dataclass-like object constructor.

    For example, some `foo: Annotated[Object, Arg(parse[json.loads, splat_arguments])]` annotation
    would unpack the result of `json.loads` into the constructor of `Object`, like `Object(**data)`.
    """
    origin = type_view.strip_optional().fallback_origin
    mapper = origin

    value_type_view = TypeView(type(value))
    if value_type_view.is_mapping:
        return origin(**value)  # pyright: ignore

    if value_type_view.is_collection and not value_type_view.is_subclass_of(str):
        return origin(*value)  # pyright: ignore

    return mapper(value)


def _as_type_view(typ: type[T] | TypeView[type[T]]) -> TypeView[type[T]]:
    if isinstance(typ, TypeView):
        return typ
    return TypeView(typ)


def default_parse(value: str, type_view: TypeView[Any]) -> Any:
    """Perform the default inferred parse behavior of cappa's type inference system."""
    parser: Parser[Any] = parse_value(type_view)
    return parser(value)


def parse_value(typ: MaybeTypeView[T]) -> Parser[T]:
    """Create a value parser for the given annotation.

    Examples:
        >>> from typing import List, Literal, Tuple
        >>> list_parser = parse_value(List[int])
        >>> tuple_parser = parse_value(Tuple[int, ...])
        >>> literal_parser = parse_literal(Literal["foo"])
    """
    type_view = _as_type_view(typ)

    if type_view.is_type_alias:
        return parse_value(type_view.strip_type_alias())

    if type_view.is_literal:
        return parse_literal(type_view)

    if type_view.is_union:
        return parse_union(type_view)

    if type_view.is_subclass_of((str, bool, int, float)):
        return type_view.annotation

    if type_view.is_none_type:
        return parse_none

    if type_view.is_subclass_of(enum.Enum):
        return parse_enum(type_view)

    if type_view.is_subclass_of(datetime):
        return datetime.fromisoformat  # type: ignore

    if type_view.is_subclass_of(date):
        return date.fromisoformat  # type: ignore

    if type_view.is_subclass_of(time):
        return time.fromisoformat  # type: ignore

    if type_view.is_subclass_of(list):
        return parse_list(type_view)  # type: ignore

    if type_view.is_subclass_of(set):
        return parse_set(type_view)  # type: ignore

    if type_view.is_subclass_of(tuple):
        return parse_tuple(type_view)  # type: ignore

    if type_view.is_subclass_of((TextIO, BinaryIO)):
        return parse_file_io(type_view)

    return type_view.annotation


def parse_literal(typ: MaybeTypeView[T]) -> Parser[T]:
    """Create a value parser for a given literal value."""
    type_view = _as_type_view(typ)
    unique_type_args = set(type_view.args)

    def literal_mapper(value: T) -> T:
        if isinstance(value, (list, set, tuple)):
            for item in cast(Sequence[Any], value):
                if item not in unique_type_args:
                    raise choices_error(type_view.args, item)

            return cast(T, value)

        if value in unique_type_args:
            return value

        for type_arg in unique_type_args:
            raw_value = str(type_arg)
            if raw_value == value:
                return type_arg

        raise choices_error(type_view.args, value)

    return literal_mapper


def parse_enum(typ: MaybeTypeView[T]):
    type_view = _as_type_view(typ)
    choices: tuple[Any, ...] = tuple(v.value for v in type_view.annotation)

    def enum_mapper(value: Any) -> Any:
        try:
            return type_view.annotation(value)
        except ValueError:
            raise choices_error(choices, value)

    return enum_mapper


def parse_list(typ: MaybeTypeView[list[T]]) -> Parser[list[T]]:
    """Create a value parser for a list of given type `of_type`."""
    type_view = _as_type_view(typ)
    inner_mapper: Parser[T] = parse_value(type_view.inner_types[0])

    def list_mapper(value: list[Any]) -> list[T]:
        return [inner_mapper(v) for v in value]

    return list_mapper


def parse_set(typ: MaybeTypeView[list[T]]) -> Parser[set[T]]:
    """Create a value parser for a list of given type `of_type`."""
    type_view = _as_type_view(typ)
    inner_mapper: Parser[T] = parse_value(type_view.inner_types[0])

    def set_mapper(value: list[Any]) -> set[T]:
        return {inner_mapper(v) for v in value}

    return set_mapper


def parse_tuple(typ: MaybeTypeView[T]) -> Parser[tuple[T]]:
    """Create a value parser for a tuple with type-args of given `type_args`."""
    type_view = _as_type_view(typ)
    if type_view.is_variadic_tuple:
        assert type_view.args
        inner_type = type_view.args[0]
        list_mapper = parse_list(List[inner_type])  # type: ignore

        def unbounded_tuple_mapper(value: list[Any]) -> tuple[Any, ...]:
            return tuple(list_mapper(value))

        return unbounded_tuple_mapper

    def tuple_mapper(value: list[Any]) -> tuple[Any]:
        result: list[Any] = []
        for inner_type, inner_value in zip(type_view.inner_types, value):
            inner_mapper: Parser[T] = parse_value(inner_type)
            inner_value = inner_mapper(inner_value)
            result.append(inner_value)
        return tuple(result)

    return tuple_mapper


def parse_union(typ: MaybeTypeView[T]) -> Parser[T]:
    """Create a value parser for a Union with type-args of given `type_args`."""

    def type_priority_key(type_type_view: TypeView[Any]) -> int:
        return type_priority.get(type_type_view.annotation, 1)

    def union_mapper(value: Any) -> Any:
        exceptions: list[str] = []
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

    type_view = _as_type_view(typ)
    mappers: list[tuple[TypeView[T], Callable[..., Any]]] = [
        (t, parse_value(t))
        for t in sorted(type_view.inner_types, key=type_priority_key)
    ]

    return union_mapper


def parse_none(value: Any) -> Never:
    """Create a value parser for None.

    Default values are not run through Arg.parse, so there's no way to arrive at a `None` value.
    """
    raise ValueError(value)


def parse_file_io(typ: MaybeTypeView[T]) -> Parser[T]:
    type_view = _as_type_view(typ)

    def file_io_mapper(value: str) -> T:
        try:
            file_mode: FileMode = next(
                f for f in type_view.metadata if isinstance(f, FileMode)
            )
        except StopIteration:
            file_mode = FileMode()

            if type_view.is_subclass_of(BinaryIO):
                file_mode.mode += "b"

        return file_mode(value)  # type: ignore

    return file_io_mapper


def evaluate_parse(
    parsers: Parser[T] | Sequence[Parser[Any]],
    type_view: TypeView[T],
    state: State[S] | None = None,
) -> Callable[..., T]:
    from cappa.invoke import fulfill_deps

    state = State.ensure(state)  # type: ignore

    if callable(parsers):
        parsers = [parsers]

    parsers = [
        functools.partial(
            parser,
            **fulfill_deps(
                parser,
                {TypeView: type_view, State: state},
                allow_empty=True,
            ).kwargs,
        )
        for parser in parsers
    ]

    if len(parsers) == 1:
        return parsers[0]

    def sequence_parsers(value: Any) -> T:
        result = value
        for parser in parsers:
            result = parser(result)

        return result

    return sequence_parsers


def choices_error(choices: Sequence[Any], value: Any) -> Exception:
    options = ", ".join(f"{t!r}" for t in choices)
    return ValueError(f"Invalid choice: '{value}' (choose from {options})")
