from __future__ import annotations

import argparse
import sys
import typing

from cappa.arg_def import ArgAction, ArgDefinition
from cappa.command import Command
from cappa.command_def import CommandDefinition, Subcommands

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

    def __getattr__(self, name):
        if "." in name:
            group, name = name.split(".", 1)
            try:
                ns = self.__dict__[group]
            except KeyError:
                raise AttributeError
            return getattr(ns, name)

        raise AttributeError


def render(
    command_def: CommandDefinition[T], argv: list[str], exit_with=None
) -> tuple[Command[T], dict[str, typing.Any]]:
    parser = create_parser(command_def, exit_with)

    ns = Nestedspace()
    result_namespace = parser.parse_args(argv, ns)

    result = to_dict(result_namespace)
    command = result.pop("__command__")

    return command, result


def create_parser(
    command_def: CommandDefinition, exit_with=None
) -> argparse.ArgumentParser:
    if exit_with is None:
        exit_with = sys_exit

    parser = ArgumentParser(
        prog=command_def.command.name,
        description=join_help(command_def.title, command_def.description),
        exit_on_error=False,
        exit_with=exit_with,
    )
    parser.set_defaults(__command__=command_def.command)

    add_arguments(parser, command_def)
    return parser


def add_arguments(
    parser: argparse.ArgumentParser, command_def: CommandDefinition, dest_prefix=""
):
    for arg_def in command_def.arguments:
        if isinstance(arg_def, ArgDefinition):
            add_argument(parser, arg_def, dest_prefix=dest_prefix)
        elif isinstance(arg_def, Subcommands):
            add_subcommands(parser, arg_def, dest_prefix=dest_prefix)
        else:
            raise NotImplementedError()


def add_argument(
    parser: argparse.ArgumentParser, arg_def: ArgDefinition, dest_prefix=""
):
    dash_name = arg_def.name.replace("_", "-")
    names: list[str] = []
    if arg_def.arg.short:
        if isinstance(arg_def.arg.short, bool):
            short_name = f"-{dash_name[0]}"
        else:
            short_name = arg_def.arg.short

        names.append(short_name)

    if arg_def.arg.long:
        if isinstance(arg_def.arg.long, bool):
            long_name = f"--{dash_name}"
        else:
            long_name = arg_def.arg.long

        names.append(long_name)

    num_args = render_num_args(arg_def.num_args)
    action = arg_def.action.value
    kwargs: dict[str, typing.Any] = {
        "action": action,
        "dest": dest_prefix + arg_def.name,
        "help": arg_def.help,
    }

    if arg_def.arg.required and names:
        kwargs["required"] = arg_def.arg.required

    if arg_def.arg.default is not ...:
        kwargs["default"] = arg_def.arg.default

    if arg_def.action is not arg_def.action.store_true:
        kwargs["nargs"] = num_args
        kwargs["type"] = arg_def.arg.parser

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
        )
        subparser.set_defaults(
            __command__=subcommand.command, **{nested_dest_prefix + "__name__": name}
        )

        add_arguments(
            subparser,
            subcommand,
            dest_prefix=nested_dest_prefix,
        )


def render_action(action: ArgAction):
    mapping: dict[ArgAction, str] = {
        ArgAction.set: "store",
        ArgAction.append: "append",
        ArgAction.store_true: "store_true",
    }
    return mapping[action]


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
