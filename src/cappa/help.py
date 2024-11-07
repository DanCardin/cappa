from __future__ import annotations

import typing
from collections.abc import Iterable
from dataclasses import dataclass, replace
from itertools import groupby

from rich.console import NewLine
from rich.markdown import Markdown
from rich.padding import Padding
from rich.table import Table
from rich.text import Text
from typing_extensions import Self, TypeAlias

from cappa.arg import Arg, ArgAction, Group
from cappa.output import Displayable
from cappa.subcommand import Subcommand
from cappa.type_view import Empty
from cappa.typing import assert_type

if typing.TYPE_CHECKING:
    from cappa.command import Command

HelpFormatable: TypeAlias = typing.Callable[["Command", str], typing.List[Displayable]]
ArgGroup: TypeAlias = typing.Tuple[
    typing.Tuple[str, bool], typing.List[typing.Union[Arg, Subcommand]]
]
Dimension: TypeAlias = typing.Tuple[int, int, int, int]
ArgFormat: TypeAlias = typing.Union[
    str,
    typing.Sequence[typing.Union[str, typing.Callable[[Arg], typing.Union[str, None]]]],
    typing.Callable[[Arg], typing.Union[str, None]],
]


def create_version_arg(version: str | Arg | None = None) -> Arg | None:
    if not version:
        return None

    if isinstance(version, str):
        version = Arg(
            value_name=version,
            short=["-v"],
            long=["--version"],
            help="Show the version and exit.",
            group=Group(1, "Help", section=2),
            action=ArgAction.version,
        )

    if version.value_name is Empty:
        raise ValueError(
            "Expected explicit version `Arg` to supply version number as its name, like `Arg('1.2.3', ...)`"
        )

    if version.long is True:
        version.long = "--version"

    return version.normalize(
        action=ArgAction.version, field_name="version", default=None
    )


def create_help_arg(help: bool | Arg | None = True) -> Arg | None:
    if not help:
        return None

    if isinstance(help, bool):
        help = Arg(
            short=["-h"],
            long=["--help"],
            help="Show this message and exit.",
            group=Group(0, "Help", section=2),
            action=ArgAction.help,
        )

    return help.normalize(action=ArgAction.help, field_name="help", default=None)


def create_completion_arg(completion: bool | Arg = True) -> Arg | None:
    if not completion:
        return None

    if isinstance(completion, bool):
        completion = Arg(
            long=["--completion"],
            choices=["generate", "complete"],
            group=Group(2, "Help", section=2),
            help="Use `--completion generate` to print shell-specific completion source.",
            action=ArgAction.completion,
        )

    return completion.normalize(
        field_name="completion",
        action=ArgAction.completion,
        default=None,
    )


@dataclass(frozen=True)
class HelpFormatter:
    left_padding: Dimension = (0, 0, 0, 2)
    arg_format: ArgFormat = ("{help}", "{choices}", "{default}")
    default_format: str = "(Default: {default})"

    default: typing.ClassVar[Self]

    def __call__(self, command: Command, prog: str) -> list[Displayable]:
        arg_groups = generate_arg_groups(command)

        lines: list[Displayable] = []
        lines.append(add_short_args(prog, arg_groups))

        if command.help:
            lines.append(NewLine())
            lines.append(Padding(Markdown(f"**{command.help}**"), self.left_padding))
        if command.description:
            lines.append(NewLine())
            lines.append(Padding(Markdown(command.description), self.left_padding))

        lines.extend(add_long_args(self, arg_groups))
        return lines

    def with_arg_format(self, format: ArgFormat) -> Self:
        return replace(self, arg_format=format)

    def with_default_format(self, format: str) -> Self:
        return replace(self, default_format=format)


HelpFormatter.default = HelpFormatter()


def add_long_args(help_formatter: HelpFormatter, arg_groups: list[ArgGroup]) -> list:
    table = Table(box=None, expand=False, padding=help_formatter.left_padding)
    table.add_column(justify="left", ratio=1)
    table.add_column(style="cappa.help", ratio=2)

    for (group_name, _), args in arg_groups:
        table.add_row(
            Text(group_name, style="cappa.group", justify="left"),
            Text(style="cappa.group"),
        )
        for arg in args:
            if isinstance(arg, Arg):
                table.add_row(
                    Padding(format_arg_name(arg, ", "), help_formatter.left_padding),
                    Markdown(format_arg(help_formatter, arg), style=""),
                )
            else:
                for option in arg.available_options():
                    table.add_row(*format_subcommand(help_formatter, option))

        table.add_row()

    return [table]


def format_arg(help_formatter: HelpFormatter, arg: Arg) -> str:
    arg_format = help_formatter.arg_format
    if not isinstance(arg_format, Iterable) or isinstance(arg_format, str):
        arg_format = (arg_format,)

    segments = []
    for format_segment in arg_format:
        default = ""
        if arg.show_default and arg.default is not None and arg.default is not Empty:
            default = help_formatter.default_format.format(default=arg.default)

        choices = ""
        if arg.choices:
            choices = "Valid options: " + ", ".join(arg.choices) + "."

        context = {
            "help": arg.help or "",
            "default": default,
            "choices": choices,
            "arg": arg,
        }

        if callable(format_segment):
            segment = format_segment(arg)
        else:
            segment = format_segment.format(**context)

        if segment:
            segments.append(segment)

    return " ".join(segments)


def format_subcommand(help_formatter: HelpFormatter, command: Command):
    return (
        Padding(
            f"[cappa.subcommand]{command.real_name()}[/cappa.subcommand]",
            help_formatter.left_padding,
        ),
        command.help,
    )


def format_short_help(command: Command, prog: str) -> Displayable:
    arg_groups = generate_arg_groups(command)
    return add_short_args(prog, arg_groups)


def generate_arg_groups(command: Command, include_hidden=False) -> list[ArgGroup]:
    def by_group_key(arg: Arg | Subcommand):
        return assert_type(arg.group, Group).key

    def by_group(arg: Arg | Subcommand):
        group = assert_type(arg.group, Group)
        return (group.name, group.exclusive)

    sorted_args = sorted(command.arguments, key=by_group_key)
    return [
        (g, [a for a in args if include_hidden or not a.hidden])
        for g, args in groupby(sorted_args, key=by_group)
    ]


def add_short_args(prog: str, arg_groups: list[ArgGroup]) -> str:
    segments: list[str] = [f"Usage: {prog}"]
    for _, args in arg_groups:
        for arg in args:
            segments.append(format_arg_name(arg, ", ", n=1))

    return " ".join(segments)


def format_arg_name(arg: Arg | Subcommand, delimiter, *, n=0) -> str:
    if isinstance(arg, Arg):
        is_option = arg.short or arg.long
        has_value = not ArgAction.is_non_value_consuming(arg.action)

        arg_names = arg.names_str(delimiter, n=n)
        if not is_option:
            arg_names = arg_names.upper()

        text = f"[cappa.arg]{arg_names}[/cappa.arg]"

        if is_option and has_value:
            name = typing.cast(str, arg.value_name).upper()
            text = f"{text} [cappa.arg.name]{name}[/cappa.arg.name]"

        if not arg.required:
            return rf"\[{text}]"

        return text

    arg_names = arg.names_str(",")
    return f"{{[cappa.subcommand]{arg_names}[/cappa.subcommand]}}"


def format_subcommand_names(names: list[str]):
    return ", ".join(f"[cappa.subcommand]{a}[/cappa.subcommand]" for a in names)
