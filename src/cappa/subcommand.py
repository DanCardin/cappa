from __future__ import annotations

import dataclasses
import typing

from typing_extensions import Annotated, Self, TypeAlias
from typing_inspect import is_optional_type, is_union_type

from cappa.arg import Group
from cappa.class_inspect import Field, extract_dataclass_metadata
from cappa.completion.types import Completion
from cappa.typing import (
    MISSING,
    NoneType,
    T,
    assert_type,
    find_type_annotation,
    missing,
)

if typing.TYPE_CHECKING:
    from cappa.command import Command
    from cappa.help import HelpFormatable


@dataclasses.dataclass
class Subcommand:
    """Describe a CLI subcommand.

    Arguments:
        name: Defaults to the name of the class, converted to dash case, but
            can be overridden here.
        types: Defaults to the class's annotated types, but can be overridden here.
        required: Defaults to automatically inferring requiredness, based on whether the
            class's value has a default. By setting this, you can force a particular value.
        hidden: Whether the argument should be hidden in help text. Defaults to False.
    """

    field_name: str | MISSING = ...
    required: bool | None = None
    group: str | tuple[int, str] | Group = (3, "Subcommands")
    hidden: bool = False

    types: typing.Iterable[type] | MISSING = ...
    options: dict[str, Command] = dataclasses.field(default_factory=dict)

    @classmethod
    def collect(
        cls, field: Field, type_hint: type, help_formatter: HelpFormatable | None = None
    ) -> Subcommand | None:
        object_annotation = find_type_annotation(type_hint, Subcommand)
        subcommand = object_annotation.obj

        field_metadata = extract_dataclass_metadata(field, Subcommand)
        if field_metadata:
            subcommand = [field_metadata]

        if not subcommand:
            return None

        assert len(subcommand) == 1
        return subcommand[0].normalize(
            object_annotation.annotation,
            field_name=field.name,
            help_formatter=help_formatter,
        )

    def normalize(
        self,
        annotation=NoneType,
        field_name: str | None = None,
        help_formatter: HelpFormatable | None = None,
    ) -> Self:
        field_name = field_name or assert_type(self.field_name, str)
        types = infer_types(self, annotation)
        required = infer_required(self, annotation)
        options = infer_options(self, types, help_formatter=help_formatter)
        group = infer_group(self)

        return dataclasses.replace(
            self,
            field_name=field_name,
            types=types,
            required=required,
            options=options,
            group=group,
        )

    def map_result(self, prog: str, parsed_args):
        option_name = parsed_args.pop("__name__")
        option = self.options[option_name]
        return option.map_result(option, prog, parsed_args)

    def available_options(self) -> list[Command]:
        return [o for o in self.options.values() if not o.hidden]

    def names(self) -> list[str]:
        return [n for n, o in self.options.items() if not o.hidden]

    def names_str(self, delimiter: str = ", ") -> str:
        return f"{delimiter.join(self.names())}"

    def completion(self, partial: str):
        return [Completion(o) for o in self.options if partial in o]


def infer_types(arg: Subcommand, annotation: type) -> typing.Iterable[type]:
    if arg.types is not missing:
        return typing.cast(typing.Iterable[type], arg.types)

    if is_union_type(annotation):
        types = typing.get_args(annotation)
        return tuple([t for t in types if not is_optional_type(t)])

    return (annotation,)


def infer_required(arg: Subcommand, annotation: type) -> bool:
    if arg.required is not None:
        return arg.required

    return not is_optional_type(annotation)


def infer_options(
    arg: Subcommand,
    types: typing.Iterable[type],
    help_formatter: HelpFormatable | None = None,
) -> dict[str, Command]:
    from cappa.command import Command

    if arg.options:
        return {
            name: Command.collect(type_command)
            for name, type_command in arg.options.items()
        }

    options = {}
    for type_ in types:
        type_command: Command = Command.get(type_, help_formatter=help_formatter)
        type_name = type_command.real_name()
        options[type_name] = Command.collect(type_command)

    return options


def infer_group(arg: Subcommand) -> Group:
    name = None
    order = 3

    if isinstance(arg.group, Group):
        return arg.group

    if isinstance(arg.group, str):
        name = arg.group

    if isinstance(arg.group, tuple):
        order, name = arg.group

    assert name
    return Group(name=name, order=order)


Subcommands: TypeAlias = Annotated[T, Subcommand]
