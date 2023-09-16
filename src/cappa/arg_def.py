"""Define the internal types produced by the public API types.

The internal `ArgDefinition` API has a necessarily literal interface. Instead, users construct `Arg`
instances with associated type annotations, which are rendered into `ArgDefinition`
instances; which are ultimately routed into the argument parser.
"""
from __future__ import annotations

import dataclasses
import enum
import types
import typing
from collections.abc import Callable
from typing import Generic, Type, TypeVar

from typing_inspect import is_literal_type, is_union_type

from cappa.arg import Arg
from cappa.class_inspect import Field
from cappa.typing import render_type

T = TypeVar("T")


@enum.unique
class ArgAction(enum.Enum):
    set = "store"
    store_true = "store_true"
    store_false = "store_false"
    append = "append"
    count = "count"


@dataclasses.dataclass
class ArgDefinition(Generic[T]):
    name: str
    arg: Arg[T]

    type: Callable
    action: ArgAction
    num_args: int | None = None
    map_result: Callable | None = None
    help: str | None = None

    @classmethod
    def collect(
        cls, field: Field, raw_type_hint: Type, help: str | None = None
    ) -> ArgDefinition[T] | None:
        maybe_arg: tuple[Arg, type] = Arg.collect(field, raw_type_hint)
        arg, type_hint = maybe_arg

        typ = typing.get_origin(type_hint) or type_hint
        type_args = typing.get_args(type_hint)

        num_args = None
        action = ArgAction.set

        if not is_union_type(typ):
            # XXX: Enums should coerce, basically `typ`, which obviates choices.

            if issubclass(typ, bool):
                arg = dataclasses.replace(arg, long=True)
                action = ArgAction.store_true

            if issubclass(typ, list):
                action = ArgAction.append

            if issubclass(typ, tuple):
                num_args = len(type_args)

        map_result = generate_map_result(typ, type_args)

        return cls(
            name=field.name,
            arg=arg,
            type=type_hint,
            action=action,
            num_args=num_args,
            map_result=map_result,
            help=arg.help or help,
        )


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

    if is_union_type(type_) or issubclass(type_, types.UnionType):
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
                f"Could not map '{value}' given options: {', '.join(render_type(t) for t in type_args)}"
            )

        return union_mapper

    if issubclass(type_, (str, bool, int, float)):
        return type_

    if issubclass(type_, types.NoneType):

        def map_none(value):
            if value is None:
                return

            raise ValueError(value)

        return map_none

    if issubclass(type_, list):
        assert type_args

        inner_type = type_args[0]
        inner_mapper = generate_map_result(inner_type, typing.get_args(inner_type))

        def list_mapper(value: list):
            return [inner_mapper(v) for v in value]

        return list_mapper

    if issubclass(type_, tuple):
        assert type_args

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

    if dataclasses.is_dataclass(type_):

        def dataclass_mapper(value):
            return type_(**value)

        return dataclass_mapper

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
