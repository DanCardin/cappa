from __future__ import annotations

import dataclasses
import sys
import typing

from typing_extensions import dataclass_transform

from cappa.arg import Arg
from cappa.class_inspect import detect
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

    _, _, instance = Command.parse_command(
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
    deps: typing.Sequence[typing.Callable] | None = None,
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
        deps: Optional extra depdnencies to load ahead of invoke processing. These
            deps are evaulated in order and unconditionally.
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

    command, parsed_command, instance = Command.parse_command(
        command,
        argv=argv,
        render=render,
        exit_with=exit_with,
        color=color,
        version=version,
        help=help,
    )

    return invoke_callable(command, parsed_command, instance, deps=deps)


@dataclass_transform()
def command(
    *,
    name: str | None = None,
    help: str | None = None,
    description: str | None = None,
    invoke: typing.Callable | str | None = None,
):
    """Register a cappa CLI command/subcomment.

    Args:
        name: The name of the command. If omitted, the name of the command
            will be the name of the `cls`, converted to dash-case.
        help: Optional help text. If omitted, the `cls` docstring will be parsed,
            and the headline section will be used to document the command
            itself, and the arguments section will become the default help text for
            any params/options.
        description: Optional extended help text. If omitted, the `cls` docstring will
            be parsed, and the extended long description section will be used.
        invoke: Optional command to be called in the event parsing is successful.
            In the case of subcommands, it will only call the parsed/selected
            function to invoke.
    """

    def wrapper(_decorated_cls):
        if not detect(_decorated_cls):
            _decorated_cls = dataclasses.dataclass(_decorated_cls)

        instance = Command(
            cmd_cls=_decorated_cls,
            invoke=invoke,
            name=name,
            help=help,
            description=description,
        )
        _decorated_cls.__cappa__ = instance
        return _decorated_cls

    return wrapper
