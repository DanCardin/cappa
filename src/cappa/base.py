from __future__ import annotations

import sys
import typing

from cappa.arg import Arg
from cappa.command import Command
from cappa.invoke import invoke_callable

T = typing.TypeVar("T")


def parse(
    obj: type[T],
    *,
    argv: list[str] | None = None,
    render: typing.Callable | None = None,
    exit_with=None,
    color: bool = True,
    version: str | Arg | None = None,
    help: bool | Arg = True,
) -> T:
    """Parse the command, returning an instance of `obj`.

    In the event that a subcommand is selected, only the selected subcommand
    function is invoked.

    Arguments:
        obj: A class which can represent a CLI command chain.
        argv: Defaults to the process argv. This command is generally only
            necessary when testing.
        render: A function used to perform the underlying parsing and return a raw
            parsed state. This defaults to constructing built-in function using argparse.
        exit_with: Used when parsing fails, to raise/indicate failure. By default, exits
            with SystemExit to kill the process.
        color: Whether to output in color, if the `color` extra is installed.
        version: If a string is supplied, adds a -v/--version flag which returns the
            given version string. If an `Arg` is supplied, uses the `name`/`short`/`long`/`help`
            fields to add a corresponding version argument.
        help: If `True` (default to True), adds a -h/--help flag. If an `Arg` is supplied,
            uses the `short`/`long`/`help` fields to add a corresponding help argument.
    """
    if argv is None:  # pragma: no cover
        argv = sys.argv

    command = Command.get(obj)
    _, instance = Command.parse_command(
        command,
        argv=argv,
        render=render,
        exit_with=exit_with,
        color=color,
        version=version,
        help=help,
    )
    return instance


def invoke(
    obj: type,
    *,
    argv: list[str] | None = None,
    render: typing.Callable | None = None,
    exit_with=None,
    color: bool = True,
    version: str | Arg | None = None,
    help: bool | Arg = True,
):
    """Parse the command, and invoke the selected command or subcommand.

    In the event that a subcommand is selected, only the selected subcommand
    function is invoked.

    Arguments:
        obj: A class which can represent a CLI command chain.
        argv: Defaults to the process argv. This command is generally only
            necessary when testing.
        render: A function used to perform the underlying parsing and return a raw
            parsed state. This defaults to constructing built-in function using argparse.
        exit_with: Used when parsing fails, to raise/indicate failure. By default, exits
            with SystemExit to kill the process.
        color: Whether to output in color, if the `color` extra is installed.
        version: If a string is supplied, adds a -v/--version flag which returns the
            given version string. If an `Arg` is supplied, uses the `name`/`short`/`long`
            fields to add a corresponding version argument.
        help: If `True` (default to True), adds a -h/--help flag. If an `Arg` is supplied,
            uses the `short`/`long`/`help` fields to add a corresponding help argument.
    """
    if argv is None:  # pragma: no cover
        argv = sys.argv

    command: Command = Command.get(obj)

    parsed_command, instance = Command.parse_command(
        command,
        argv=argv,
        render=render,
        exit_with=exit_with,
        color=color,
        version=version,
        help=help,
    )

    return invoke_callable(parsed_command, instance)
