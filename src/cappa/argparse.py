from __future__ import annotations

import argparse
import sys
import typing

from typing_extensions import assert_never

from cappa.arg import Arg
from cappa.command import Command
from cappa.command_def import CommandDefinition, Subcommands
from cappa.typing import assert_not_missing, assert_type

try:
    from rich import print
except ImportError:  # pragma: no cover
    pass


T = typing.TypeVar("T")


def sys_exit(status, _):
    sys.exit(status)


def value_error(_, message):
    raise ValueError(message)


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, exit_with=sys_exit, **kwargs):
        self.exit_with = exit_with
        super().__init__(*args, **kwargs)

    def exit(self, status=0, message=None):
        if message:
            self._print_message(message, sys.stderr)
        self.exit_with(status, message)


class Nestedspace(argparse.Namespace):
    def __setattr__(self, name, value):
        if "." in name:
            group, name = name.split(".", 1)
            ns = getattr(self, group, Nestedspace())
            setattr(ns, name, value)
            self.__dict__[group] = ns
        else:
            self.__dict__[name] = value


def render(
    command_def: CommandDefinition[T],
    argv: list[str],
    exit_with=None,
    color: bool = True,
) -> tuple[Command[T], dict[str, typing.Any]]:
    if exit_with is None:
        exit_with = sys_exit

    parser = create_parser(command_def, exit_with, color=color)

    ns = Nestedspace()

    try:
        result_namespace = parser.parse_args(argv[1:], ns)
    except argparse.ArgumentError as e:
        message = str(e)
        print(str(e))
        raise exit_with(127, message)

    result = to_dict(result_namespace)
    command = result.pop("__command__")

    return command, result


def create_parser(
    command_def: CommandDefinition, exit_with: typing.Callable, color: bool = True
) -> argparse.ArgumentParser:
    parser = ArgumentParser(
        prog=command_def.command.name,
        description=join_help(command_def.title, command_def.description),
        exit_on_error=False,
        exit_with=exit_with,
        allow_abbrev=False,
        formatter_class=choose_help_formatter(color=color),
    )
    parser.set_defaults(__command__=command_def.command)

    add_arguments(parser, command_def)
    return parser


def choose_help_formatter(color: bool = True):
    help_formatter: type[
        argparse.HelpFormatter
    ] = argparse.ArgumentDefaultsHelpFormatter

    if color is True:
        try:
            from rich_argparse import ArgumentDefaultsRichHelpFormatter

            help_formatter = ArgumentDefaultsRichHelpFormatter
        except ImportError:  # pragma: no cover
            pass

    return help_formatter


def add_arguments(
    parser: argparse.ArgumentParser, command_def: CommandDefinition, dest_prefix=""
):
    for arg in command_def.arguments:
        if isinstance(arg, Arg):
            add_argument(parser, arg, dest_prefix=dest_prefix)
        elif isinstance(arg, Subcommands):
            add_subcommands(parser, arg, dest_prefix=dest_prefix)
        else:
            assert_never(arg)


def add_argument(parser: argparse.ArgumentParser, arg: Arg, dest_prefix=""):
    name: str = assert_not_missing(arg.name)

    names: list[str] = []
    if arg.short:
        short = assert_type(arg.short, str)
        names.append(short)

    if arg.long:
        long = assert_type(arg.long, str)
        names.append(long)

    is_positional = not names

    num_args = render_num_args(arg.num_args)

    kwargs: dict[str, typing.Any] = {
        "action": arg.action.value,
        "dest": dest_prefix + name,
        "help": arg.help,
    }

    if is_positional:
        kwargs["metavar"] = name

    if arg.required and names:
        kwargs["required"] = arg.required

    if arg.default is not ...:
        kwargs["default"] = arg.default

    if arg.action is not arg.action.store_true:
        kwargs["nargs"] = num_args

    if arg.choices:
        kwargs["choices"] = arg.choices

    parser.add_argument(*names, **kwargs)


def add_subcommands(
    parser: argparse.ArgumentParser,
    subcommands: Subcommands,
    dest_prefix="",
):
    subcommand_dest = subcommands.name
    subparsers = parser.add_subparsers(
        title=subcommand_dest,
        required=subcommands.required,
        description=subcommands.help,
    )

    for name, subcommand in subcommands.options.items():
        nested_dest_prefix = f"{dest_prefix}{subcommand_dest}."
        subparser = subparsers.add_parser(
            name=subcommand.command.real_name(),
            help=subcommand.title,
            description=subcommand.description,
            formatter_class=parser.formatter_class,
        )
        subparser.set_defaults(
            __command__=subcommand.command, **{nested_dest_prefix + "__name__": name}
        )

        add_arguments(
            subparser,
            subcommand,
            dest_prefix=nested_dest_prefix,
        )


def render_num_args(num_args: int | None) -> int | str | None:
    if num_args is None:
        return None

    if num_args == -1:
        return "+"

    return num_args


def to_dict(value: argparse.Namespace):
    result = {}
    for k, v in value.__dict__.items():
        if isinstance(v, argparse.Namespace):
            v = to_dict(v)
        result[k] = v

    return result


def join_help(*segments):
    return " ".join([s for s in segments if s])
