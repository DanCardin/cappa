from __future__ import annotations

import typing
from itertools import groupby

from rich.console import NewLine
from rich.table import Table
from rich.text import Text
from typing_extensions import TypeAlias

from cappa.arg import Arg, ArgAction, no_extra_arg_actions
from cappa.command import Command
from cappa.output import Displayable
from cappa.subcommand import Subcommand

ArgGroup: TypeAlias = typing.Tuple[str, typing.List[typing.Union[Arg, Subcommand]]]


def create_version_arg(version: str | Arg | None = None) -> Arg | None:
    if not version:
        return None

    if isinstance(version, str):
        version = Arg(
            version,
            short=["-v"],
            long=["--version"],
            help="Show the version and exit.",
            group=(3, "Help"),
        )

    return version.normalize(action=ArgAction.version)


def create_help_arg(help: bool | Arg | None = True) -> Arg | None:
    if not help:
        return None

    if isinstance(help, bool):
        help = Arg(
            name="help",
            short=["-h"],
            long=["--help"],
            help="Show this message and exit.",
            group=(3, "Help"),
        )

    return help.normalize(action=ArgAction.help, name="help")


def create_completion_arg(completion: bool | Arg = True) -> Arg | None:
    if not completion:
        return None

    if isinstance(completion, bool):
        completion = Arg(
            name="completion",
            long=["--completion"],
            choices=["generate", "complete"],
            group=(3, "Help"),
            help="Use `--completion generate` to print shell-specific completion source",
        ).normalize()

    return completion.normalize(action=ArgAction.completion)


def format_help(command: Command, prog: str) -> list[Displayable]:
    arg_groups = generate_arg_groups(command)

    lines: list[Displayable] = []
    lines.append(add_short_args(prog, arg_groups))

    desc = " ".join([s for s in [command.help, command.description] if s])
    if desc:
        lines.append(NewLine())
        lines.append(Text(desc))

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
            segments.append(format_arg_name(arg, ", "))

    return " ".join(segments)


def add_long_args(arg_groups: list[ArgGroup]) -> list:
    table = Table(box=None)
    table.add_column(style="cappa.arg", justify="right")
    table.add_column(style="cappa.help")

    for group, args in arg_groups:
        table.add_row(
            Text(group, style="cappa.group", justify="right"),
            Text(style="cappa.group"),
        )
        for arg in args:
            table.add_row(format_arg_name(arg, "/"), arg.help)

        table.add_row()

    return [table]


def format_arg_name(arg: Arg | Subcommand, delimiter) -> str:
    if isinstance(arg, Arg):
        arg_names = arg.names_str(delimiter)
        text = f"[cappa.arg]{arg_names}[/cappa.arg]"

        is_option = arg.short or arg.long
        has_value = arg.action not in no_extra_arg_actions
        if is_option and has_value:
            text = f"{text} [cappa.arg.name]{arg.name}[/cappa.arg.name]"

        if not arg.required:
            return rf"\[{text}]"

        return text

    arg_names = arg.names_str(",")
    return f"[cappa.subcommand]{arg_names}[/cappa.subcommand]"
