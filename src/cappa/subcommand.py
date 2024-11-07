from __future__ import annotations

import dataclasses
import typing

from typing_extensions import Annotated, Self, TypeAlias

from cappa.arg import Group
from cappa.class_inspect import Field, extract_dataclass_metadata
from cappa.completion.types import Completion
from cappa.type_view import Empty, EmptyType, TypeView
from cappa.typing import T, assert_type, find_annotations

if typing.TYPE_CHECKING:
    from cappa.command import Command
    from cappa.help import HelpFormatable


DEFAULT_SUBCOMMAND_GROUP = Group(3, "Subcommands", section=1)


@dataclasses.dataclass
class Subcommand:
    """Describe a CLI subcommand.

    Arguments:
        field_name: Defaults to the name of the class, converted to dash case, but
            can be overridden here.
        required: Defaults to automatically inferring requiredness, based on whether the
            class's value has a default. By setting this, you can force a particular value.
        group: The subcommand group, for use in controlling help text for the subcommand, and
            where it is displayed. This can be any of: the string name (``'Subcommands'``),
            a 2-tuple of the `order` and the name (``(3, "Subcommands")``), or a :class:`Group`
            instance (``Group(3, 'Subcommands')``)
        hidden: Whether the argument should be hidden in help text. Defaults to False.
        options: A mapping of the subcommand names to the corresponding `Command` to which
            the subcommands refer. Unless imperatively constructing the CLI structure, this
            field should generally always be inferred automatically.
        types: Defaults to the class's annotated types, but can be overridden here.
    """

    field_name: str | EmptyType = Empty
    required: bool | None = None
    group: str | tuple[int, str] | Group = DEFAULT_SUBCOMMAND_GROUP
    hidden: bool = False

    options: dict[str, Command] = dataclasses.field(default_factory=dict)
    types: typing.Iterable[type] | EmptyType = Empty

    @classmethod
    def collect(
        cls,
        field: Field,
        type_view: TypeView,
        help_formatter: HelpFormatable | None = None,
    ) -> Subcommand | None:
        subcommand = find_annotations(type_view, Subcommand) or None

        field_metadata = extract_dataclass_metadata(field, Subcommand)
        if field_metadata:
            subcommand = field_metadata

        if not subcommand:
            return None

        assert len(subcommand) == 1
        return subcommand[0].normalize(
            type_view,
            field_name=field.name,
            help_formatter=help_formatter,
        )

    def normalize(
        self,
        type_view: TypeView | None = None,
        field_name: str | None = None,
        help_formatter: HelpFormatable | None = None,
    ) -> Self:
        if type_view is None:
            type_view = TypeView(...)

        field_name = field_name or assert_type(self.field_name, str)
        types = infer_types(self, type_view)
        required = infer_required(self, type_view)
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


def infer_types(arg: Subcommand, type_view: TypeView) -> typing.Iterable[type]:
    if arg.types is not Empty:
        return typing.cast(typing.Iterable[type], arg.types)

    if type_view.is_union:
        return tuple(t.annotation for t in type_view.inner_types if not t.is_none_type)

    return (type_view.annotation,)


def infer_required(arg: Subcommand, annotation: TypeView) -> bool:
    if arg.required is not None:
        return arg.required

    return not annotation.is_optional


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
DEFAULT_SUBCOMMAND = Subcommand()
