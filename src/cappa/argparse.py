from __future__ import annotations

import argparse
import sys
import typing

from typing_extensions import assert_never

from cappa.arg import Arg, ArgAction
from cappa.command import Command, Subcommands
from cappa.typing import assert_not_missing, assert_type, missing

try:
    from rich import print
except ImportError:  # pragma: no cover
    pass

if sys.version_info < (3, 9):  # pragma: no cover
    # Backport https://github.com/python/cpython/pull/3680
    original_get_action_name = argparse._get_action_name

    def _get_action_name(
        argument: argparse.Action | None,
    ) -> str | None:  # pragma: no cover
        name = original_get_action_name(argument)

        assert argument
        if name is None and argument.choices:
            return "{" + ",".join(argument.choices) + "}"

        return name

    argparse._get_action_name = _get_action_name


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
    command: Command[T],
    argv: list[str],
    exit_with=None,
    color: bool = True,
    version: str | Arg | None = None,
    help: bool | Arg = True,
) -> tuple[Command[T], dict[str, typing.Any]]:
    if exit_with is None:
        exit_with = sys_exit

    parser = create_parser(command, exit_with, color=color)
    add_help_group(parser, version=version, help=help)

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
    command: Command,
    exit_with: typing.Callable,
    color: bool = True,
) -> argparse.ArgumentParser:
    kwargs: dict[str, typing.Any] = {}
    if sys.version_info >= (3, 9):  # pragma: no cover
        kwargs["exit_on_error"] = False

    parser = ArgumentParser(
        prog=command.name,
        description=join_help(command.help, command.description),
        exit_with=exit_with,
        allow_abbrev=False,
        add_help=False,
        formatter_class=choose_help_formatter(color=color),
        **kwargs,
    )
    parser.set_defaults(__command__=command)

    add_arguments(parser, command)

    return parser


def add_help_group(
    parser: argparse.ArgumentParser,
    version: str | Arg | None = None,
    help: bool | Arg = True,
):
    if not version and not help:
        return

    help_group = parser.add_argument_group("help")
    if version:
        if isinstance(version, str):
            arg: Arg = Arg(
                version, short="-v", long="--version", help="Show the version and exit."
            )
        else:
            arg = version

        add_argument(help_group, arg, version=arg.name, action=argparse._VersionAction)

    if help:
        if isinstance(help, bool):
            arg = Arg(
                name="help",
                short="-h",
                long="--help",
                help="Show this message and exit.",
            )
        else:
            arg = help
            arg.name = "help"

        add_argument(help_group, arg, action=argparse._HelpAction)


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


def add_arguments(parser: argparse.ArgumentParser, command: Command, dest_prefix=""):
    for arg in command.arguments:
        if isinstance(arg, Arg):
            add_argument(parser, arg, dest_prefix=dest_prefix)
        elif isinstance(arg, Subcommands):
            add_subcommands(parser, arg, dest_prefix=dest_prefix)
        else:
            assert_never(arg)


def add_argument(
    parser: argparse.ArgumentParser | argparse._ArgumentGroup,
    arg: Arg,
    dest_prefix="",
    **extra_kwargs,
):
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

    if not is_positional and arg.required:
        kwargs["required"] = arg.required

    if arg.default is not missing:
        if arg.action is arg.action.append:
            kwargs["default"] = list(arg.default)  # type: ignore
        else:
            kwargs["default"] = arg.default

    if (
        isinstance(arg.action, ArgAction)
        and arg.action is not arg.action.store_true
        and num_args is not None
    ):
        kwargs["nargs"] = num_args

    if arg.choices:
        kwargs["choices"] = arg.choices

    kwargs.update(extra_kwargs)

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
            name=subcommand.real_name(),
            help=subcommand.help,
            description=subcommand.description,
            formatter_class=parser.formatter_class,
        )
        subparser.set_defaults(
            __command__=subcommand, **{nested_dest_prefix + "__name__": name}
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
