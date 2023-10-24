from __future__ import annotations

import typing
from itertools import groupby

from rich.console import NewLine
from rich.markdown import Markdown
from rich.padding import Padding
from rich.table import Table
from rich.text import Text
from typing_extensions import TypeAlias

from cappa.arg import Arg, ArgAction, no_extra_arg_actions
from cappa.command import Command
from cappa.output import Displayable
from cappa.subcommand import Subcommand
from cappa.typing import missing

ArgGroup: TypeAlias = typing.Tuple[str, typing.List[typing.Union[Arg, Subcommand]]]

left_padding = (0, 0, 0, 2)


def create_version_arg(version: str | Arg | None = None) -> Arg | None:
    if not version:
        return None

    if isinstance(version, str):
        version = Arg(
            value_name=version,
            short=["-v"],
            long=["--version"],
            help="Show the version and exit.",
            group=(4, "Help"),
        )

    if version.value_name is missing:
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
            group=(4, "Help"),
        )

    return help.normalize(action=ArgAction.help, field_name="help", default=None)


def create_completion_arg(completion: bool | Arg = True) -> Arg | None:
    if not completion:
        return None

    if isinstance(completion, bool):
        completion = Arg(
            long=["--completion"],
            choices=["generate", "complete"],
            group=(4, "Help"),
            help="Use `--completion generate` to print shell-specific completion source.",
        )

    return completion.normalize(
        field_name="completion",
        action=ArgAction.completion,
        default=None,
    )


def format_help(command: Command, prog: str) -> list[Displayable]:
    arg_groups = generate_arg_groups(command)

    lines: list[Displayable] = []
    lines.append(add_short_args(prog, arg_groups))

    if command.help:
        lines.append(NewLine())
        lines.append(Padding(Markdown(f"**{command.help}**"), left_padding))
    if command.description:
        lines.append(NewLine())
        lines.append(Padding(Markdown(command.description), left_padding))

    lines.extend(add_long_args(arg_groups))
    return lines


def generate_arg_groups(command: Command, include_hidden=False) -> list[ArgGroup]:
    def by_group(arg: Arg | Subcommand) -> tuple[int, str]:
        assert isinstance(arg.group, tuple)
        return typing.cast(typing.Tuple[int, str], arg.group)

    return [
        (g, [a for a in args if include_hidden or not a.hidden])
        for (_, g), args in groupby(
            sorted(command.arguments, key=by_group), key=by_group
        )
    ]


def add_short_args(prog: str, arg_groups: list[ArgGroup]) -> str:
    segments: list[str] = [f"Usage: {prog}"]
    for _, args in arg_groups:
        for arg in args:
            segments.append(format_arg_name(arg, ", ", n=1))

    return " ".join(segments)


def add_long_args(arg_groups: list[ArgGroup]) -> list:
    table = Table(box=None, expand=False, padding=left_padding)
    table.add_column(justify="left", ratio=1)
    table.add_column(style="cappa.help", ratio=2)

    for group, args in arg_groups:
        table.add_row(
            Text(group, style="cappa.group", justify="left"),
            Text(style="cappa.group"),
        )
        for arg in args:
            if isinstance(arg, Arg):
                table.add_row(
                    Padding(format_arg_name(arg, ", "), left_padding), arg.help
                )
            else:
                for option in arg.options.values():
                    table.add_row(*format_subcommand(option))

        table.add_row()

    return [table]


def format_arg_name(arg: Arg | Subcommand, delimiter, *, n=0) -> str:
    if isinstance(arg, Arg):
        is_option = arg.short or arg.long
        has_value = arg.action not in no_extra_arg_actions

        arg_names = arg.names_str(delimiter, n=n)
        if not is_option:
            arg_names = arg_names.upper()

        text = f"[cappa.arg]{arg_names}[/cappa.arg]"

        if is_option and has_value:
            name = arg.value_name.upper()
            text = f"{text} [cappa.arg.name]{name}[/cappa.arg.name]"

        if not arg.required:
            return rf"\[{text}]"

        return text

    arg_names = arg.names_str(",")
    return f"{{[cappa.subcommand]{arg_names}[/cappa.subcommand]}}"


def format_subcommand(command: Command):
    return (
        Padding(
            f"[cappa.subcommand]{command.real_name()}[/cappa.subcommand]", left_padding
        ),
        command.help,
    )
