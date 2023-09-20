from __future__ import annotations

import enum
import typing

from typing_inspect import is_literal_type

from cappa.typing import is_none_type, is_subclass, is_union_type, render_type


def detect_choices(origin: type, type_args: tuple[type, ...]) -> list[str] | None:
    if is_subclass(origin, enum.Enum):
        assert issubclass(origin, enum.Enum)
        return [v.value for v in origin]

    if is_union_type(origin):
        if all(is_literal_type(t) for t in type_args):
            return [str(typing.get_args(t)[0]) for t in type_args]

    return None


def generate_map_result(type_: type, type_args: tuple[type, ...]) -> typing.Callable:
    if is_literal_type(type_):
        type_arg = type_args[0]
        mapping_fn = type(type_arg)

        def literal_mapper(value):
            mapped_value = mapping_fn(value)
            if mapped_value == type_arg:
                return mapped_value

            raise ValueError(f"{value} != {type_arg}")

        return literal_mapper

    if is_union_type(type_):
        mappers: list[typing.Callable] = [
            generate_map_result(t, typing.get_args(t))
            for t in sorted(type_args, key=type_priority_key)
        ]

        def union_mapper(value):
            for mapper in mappers:
                try:
                    return mapper(value)
                except ValueError:
                    pass

            raise ValueError(
                f"Could not parse '{value}' given options: {', '.join(render_type(t) for t in type_args)}"
            )

        return union_mapper

    if is_subclass(type_, (str, bool, int, float)):
        return type_

    if is_none_type(type_):

        def map_none(value):
            if value is None:
                return

            raise ValueError(value)

        return map_none

    if is_subclass(type_, list):
        assert type_args

        inner_type = type_args[0]
        inner_mapper = generate_map_result(inner_type, typing.get_args(inner_type))

        def list_mapper(value: list):
            return [inner_mapper(v) for v in value]

        return list_mapper

    if is_subclass(type_, tuple):
        assert type_args

        if len(type_args) == 2 and type_args[1] == ...:
            _list_mapper = generate_map_result(list, (type_args[0],))

            def unbounded_tuple_mapper(value: list):
                return tuple(_list_mapper(value))

            return unbounded_tuple_mapper

        def tuple_mapper(value: list):
            result = []
            for inner_type, inner_value in zip(type_args, value):
                inner_mapper = generate_map_result(
                    inner_type, typing.get_args(inner_type)
                )
                inner_value = inner_mapper(inner_value)
                result.append(inner_value)
            return tuple(result)

        return tuple_mapper

    return type_


type_priority: typing.Final = {
    None: 0,
    float: 1,
    int: 2,
    bool: 3,
    str: 4,
}


def type_priority_key(type_) -> int:
    return type_priority.get(type_, 0)
