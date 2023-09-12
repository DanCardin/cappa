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

from cappa.arg import Arg

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
        cls, field: dataclasses.Field, raw_type_hint: Type, help: str | None = None
    ) -> ArgDefinition[T] | None:
        maybe_arg: tuple[Arg, type] | None = Arg.collect(field, raw_type_hint)
        if maybe_arg is None:
            return None

        arg, type_hint = maybe_arg

        type = typing.get_origin(type_hint) or type_hint
        type_args = typing.get_args(type_hint)

        num_args = None
        action = ArgAction.set

        if issubclass(type, bool):
            arg = dataclasses.replace(arg, long=True)
            action = ArgAction.store_true

        if issubclass(type, list):
            action = ArgAction.append

        if issubclass(type, tuple):
            num_args = len(type_args)

        # XXX: Enums should coerce, basically `type`, which obviates choices.

        map_result = generate_map_result(type, type_args)

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
    if issubclass(type_, types.UnionType):
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
                f"Could not map {value} given types: {', '.join(str(t) for t in type_args)}"
            )

        return union_mapper

    if issubclass(type_, types.NoneType):

        def map_none(value):
            if value is None:
                return

            raise ValueError(value)

        return map_none

    if issubclass(type_, (str, bool, int, float)):
        return type_

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
