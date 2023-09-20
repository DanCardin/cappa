import sys
import typing

from cappa.command import Command
from cappa.command_def import CommandDefinition

T = typing.TypeVar("T")


def parse(
    obj: type[T],
    *,
    argv: list[str] | None = None,
    render: typing.Callable | None = None,
    exit_with=None,
    color: bool = True,
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
    """
    if argv is None:  # pragma: no cover
        argv = sys.argv

    instance = Command.get(obj)
    return CommandDefinition.parse(
        instance,
        argv=argv,
        render=render,
        exit_with=exit_with,
        color=color,
    )


def invoke(
    obj: type,
    *,
    argv: list[str] | None = None,
    render: typing.Callable | None = None,
    exit_with=None,
    color: bool = True,
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
    """
    if argv is None:  # pragma: no cover
        argv = sys.argv

    instance: Command = Command.get(obj)
    return CommandDefinition.invoke(
        instance,
        argv=argv,
        render=render,
        exit_with=exit_with,
        color=color,
    )
