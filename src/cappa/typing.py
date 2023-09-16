import typing

from typing_inspect import is_literal_type

T = typing.TypeVar("T")

missing = ...
MISSING: typing.TypeAlias = type(missing)  # type: ignore


def find_type_annotation(
    type_hint: typing.Type, kind: typing.Type[T]
) -> tuple[T | None, typing.Type]:
    instance = None

    if typing.get_origin(type_hint) is typing.Annotated:
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
    assert not isinstance(value, MISSING)
    return typing.cast(T, value)


def render_type(typ) -> str:
    if is_literal_type(typ):
        inner = typing.get_args(typ)[0]
        return str(inner)

    return str(typ)
