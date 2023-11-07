from __future__ import annotations

import dataclasses
import typing

from rich.theme import Theme
from typing_extensions import dataclass_transform

from cappa import argparse, parser
from cappa.class_inspect import detect
from cappa.command import Command
from cappa.help import (
    create_completion_arg,
    create_help_arg,
    create_version_arg,
)
from cappa.invoke import resolve_callable
from cappa.output import Output

if typing.TYPE_CHECKING:
    from cappa.arg import Arg

T = typing.TypeVar("T")


def parse(
    obj: type[T] | Command[T],
    *,
    argv: list[str] | None = None,
    backend: typing.Callable | None = None,
    color: bool = True,
    version: str | Arg | None = None,
    help: bool | Arg = True,
    completion: bool | Arg = True,
    theme: Theme | None = None,
    output: Output | None = None,
) -> T:
    """Parse the command, returning an instance of `obj`.

    In the event that a subcommand is selected, only the selected subcommand
    function is invoked.

    Arguments:
        obj: A class which can represent a CLI command chain.
        argv: Defaults to the process argv. This command is generally only
            necessary when testing.
        backend: A function used to perform the underlying parsing and return a raw
            parsed state. This defaults to the native cappa parser, but can be changed
            to the argparse parser at `cappa.argparse.backend`.
        color: Whether to output in color.
        version: If a string is supplied, adds a -v/--version flag which returns the
            given string as the version. If an `Arg` is supplied, uses the `name`/`short`/`long`/`help`
            fields to add a corresponding version argument. Note the `name` is assumed to **be**
            the CLI's version, e.x. `Arg('1.2.3', help="Prints the version")`.
        help: If `True` (default to True), adds a -h/--help flag. If an `Arg` is supplied,
            uses the `short`/`long`/`help` fields to add a corresponding help argument.
        completion: Enables completion when using the cappa `backend` option. If `True`
            (default to True), adds a --completion flag. An `Arg` can be supplied to customize
            the argument's behavior.
        theme: Optional rich theme to customized output formatting.
        output: Optional `Output` instance. A default `Output` will constructed if one is not provided.
            Note the `color` and `theme` arguments take precedence over manually constructed `Output`
            attributes.
    """
    _, _, instance, _ = parse_command(
        obj=obj,
        argv=argv,
        backend=backend,
        color=color,
        version=version,
        help=help,
        completion=completion,
        theme=theme,
        output=output,
    )
    return instance


def invoke(
    obj: type | Command,
    *,
    deps: typing.Sequence[typing.Callable] | None = None,
    argv: list[str] | None = None,
    backend: typing.Callable | None = None,
    color: bool = True,
    version: str | Arg | None = None,
    help: bool | Arg = True,
    completion: bool | Arg = True,
    theme: Theme | None = None,
    output: Output | None = None,
):
    """Parse the command, and invoke the selected async command or subcommand.

    In the event that a subcommand is selected, only the selected subcommand
    function is invoked.

    Arguments:
        obj: A class which can represent a CLI command chain.
        deps: Optional extra depdnencies to load ahead of invoke processing. These
            deps are evaulated in order and unconditionally.
        argv: Defaults to the process argv. This command is generally only
            necessary when testing.
        backend: A function used to perform the underlying parsing and return a raw
            parsed state. This defaults to the native cappa parser, but can be changed
            to the argparse parser at `cappa.argparse.backend`.
        color: Whether to output in color.
        version: If a string is supplied, adds a -v/--version flag which returns the
            given string as the version. If an `Arg` is supplied, uses the `name`/`short`/`long`/`help`
            fields to add a corresponding version argument. Note the `name` is assumed to **be**
            the CLI's version, e.x. `Arg('1.2.3', help="Prints the version")`.
        help: If `True` (default to True), adds a -h/--help flag. If an `Arg` is supplied,
            uses the `short`/`long`/`help` fields to add a corresponding help argument.
        completion: Enables completion when using the cappa `backend` option. If `True`
            (default to True), adds a --completion flag. An `Arg` can be supplied to customize
            the argument's behavior.
        theme: Optional rich theme to customized output formatting.
        output: Optional `Output` instance. A default `Output` will constructed if one is not provided.
            Note the `color` and `theme` arguments take precedence over manually constructed `Output`
            attributes.
    """
    command, parsed_command, instance, concrete_output = parse_command(
        obj=obj,
        argv=argv,
        backend=backend,
        color=color,
        version=version,
        help=help,
        completion=completion,
        theme=theme,
        output=output,
    )
    resolved, global_deps = resolve_callable(
        command, parsed_command, instance, output=concrete_output, deps=deps
    )
    for dep in global_deps:
        with dep.get(concrete_output):
            pass

    with resolved.get(concrete_output) as value:
        return value


async def invoke_async(
    obj: type | Command,
    *,
    deps: typing.Sequence[typing.Callable] | None = None,
    argv: list[str] | None = None,
    backend: typing.Callable | None = None,
    color: bool = True,
    version: str | Arg | None = None,
    help: bool | Arg = True,
    completion: bool | Arg = True,
    theme: Theme | None = None,
    output: Output | None = None,
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
        backend: A function used to perform the underlying parsing and return a raw
            parsed state. This defaults to the native cappa parser, but can be changed
            to the argparse parser at `cappa.argparse.backend`.
        color: Whether to output in color.
        version: If a string is supplied, adds a -v/--version flag which returns the
            given string as the version. If an `Arg` is supplied, uses the `name`/`short`/`long`/`help`
            fields to add a corresponding version argument. Note the `name` is assumed to **be**
            the CLI's version, e.x. `Arg('1.2.3', help="Prints the version")`.
        help: If `True` (default to True), adds a -h/--help flag. If an `Arg` is supplied,
            uses the `short`/`long`/`help` fields to add a corresponding help argument.
        completion: Enables completion when using the cappa `backend` option. If `True`
            (default to True), adds a --completion flag. An `Arg` can be supplied to customize
            the argument's behavior.
        theme: Optional rich theme to customized output formatting.
        output: Optional `Output` instance. A default `Output` will constructed if one is not provided.
            Note the `color` and `theme` arguments take precedence over manually constructed `Output`
            attributes.
    """
    command, parsed_command, instance, concrete_output = parse_command(
        obj=obj,
        argv=argv,
        backend=backend,
        color=color,
        version=version,
        help=help,
        completion=completion,
        theme=theme,
        output=output,
    )
    resolved, global_deps = resolve_callable(
        command, parsed_command, instance, output=concrete_output, deps=deps
    )
    for dep in global_deps:
        async with dep.get_async(concrete_output):
            pass

    async with resolved.get_async(concrete_output) as value:
        return value


def parse_command(
    obj: type | Command[T],
    *,
    argv: list[str] | None = None,
    backend: typing.Callable | None = None,
    color: bool = True,
    version: str | Arg | None = None,
    help: bool | Arg = True,
    completion: bool | Arg = True,
    theme: Theme | None = None,
    output: Output | None = None,
) -> tuple[Command, Command[T], T, Output]:
    concrete_backend = _coalesce_backend(backend)
    concrete_output = _coalesce_output(output, theme, color)

    command: Command = collect(
        obj,
        help=help,
        version=version,
        completion=completion,
        backend=concrete_backend,
    )
    command, parsed_command, instance = Command.parse_command(
        command,
        argv=argv,
        backend=concrete_backend,
        output=concrete_output,
    )
    return command, parsed_command, instance, concrete_output


@dataclass_transform()
def command(
    _cls=None,
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

    if _cls is not None:
        return wrapper(_cls)
    return wrapper


def collect(
    obj: type[T] | Command[T],
    *,
    backend: typing.Callable | None = None,
    version: str | Arg | None = None,
    help: bool | Arg = True,
    completion: bool | Arg = True,
) -> Command[T]:
    """Retrieve the `Command` object from a cappa-capable source class.

    Arguments:
        obj: A class which can represent a CLI command chain.
        backend: A function used to perform the underlying parsing and return a raw
            parsed state. This defaults to constructing built-in function using argparse.
        version: If a string is supplied, adds a -v/--version flag which returns the
            given string as the version. If an `Arg` is supplied, uses the `name`/`short`/`long`/`help`
            fields to add a corresponding version argument. Note the `name` is assumed to **be**
            the CLI's version, e.x. `Arg('1.2.3', help="Prints the version")`.
        help: If `True` (default to True), adds a -h/--help flag. If an `Arg` is supplied,
            uses the `short`/`long`/`help` fields to add a corresponding help argument.
        completion: Enables completion when using the cappa `backend` option. If `True`
            (default to True), adds a --completion flag. An `Arg` can be supplied to customize
            the argument's behavior.
        color: Whether to output in color.
    """
    command: Command[T] = Command.get(obj)
    command = Command.collect(command)

    concrete_backend = _coalesce_backend(backend)
    if concrete_backend is argparse.backend:
        completion = False

    help_arg = create_help_arg(help)
    version_arg = create_version_arg(version)
    completion_arg = create_completion_arg(completion)

    return command.add_meta_actions(
        help=help_arg, version=version_arg, completion=completion_arg
    )


def _coalesce_backend(backend: typing.Callable | None = None):
    if backend is None:  # pragma: no cover
        return parser.backend
    return backend


def _coalesce_output(
    output: Output | None = None, theme: Theme | None = None, color: bool = True
):
    if output is None:
        output = Output()

    output.theme(theme)

    if not color:
        output.color(False)

    return output
