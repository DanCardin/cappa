from __future__ import annotations

import dataclasses
import typing

import docstring_parser
from typing_extensions import get_type_hints

from cappa import class_inspect
from cappa.arg import Arg
from cappa.command import HasCommand
from cappa.subcommand import Subcommand
from cappa.typing import assert_not_missing

if typing.TYPE_CHECKING:
    from cappa.command import Command

T = typing.TypeVar("T")


@dataclasses.dataclass
class CommandDefinition(typing.Generic[T]):
    command: Command[T]
    arguments: list[Arg[T] | Subcommands]

    title: str | None = None
    description: str | None = None

    @classmethod
    def collect(cls, command: Command):
        command_cls = type(command)
        fields = class_inspect.fields(command.cmd_cls)
        type_hints = get_type_hints(command.cmd_cls, include_extras=True)

        title = None
        description = command.help
        arg_help_map = {}
        if not command.help:
            parsed_help = docstring_parser.parse(command.cmd_cls.__doc__ or "")
            title = parsed_help.short_description
            description = parsed_help.long_description

            arg_help_map = {
                param.arg_name: param.description for param in parsed_help.params
            }

        arguments: list[Arg | Subcommands] = []

        for field in fields:
            type_hint = type_hints[field.name]

            maybe_subcommand = Subcommand.collect(field, type_hint)
            if maybe_subcommand:
                subcommand = maybe_subcommand

                name: str = assert_not_missing(subcommand.name)
                types: typing.Iterable[type] = assert_not_missing(subcommand.types)

                options = {}
                for type_ in types:
                    type_command = command_cls.get(type_)
                    type_name = type_command.real_name()
                    options[type_name] = cls.collect(type_command)

                subcommands: Subcommands = Subcommands(
                    name=name,
                    required=subcommand.required or False,
                    help=subcommand.help,
                    options=options,
                )
                arguments.append(subcommands)

            else:
                arg_help = arg_help_map.get(field.name)
                arg_def: Arg = Arg.collect(field, type_hint, fallback_help=arg_help)
                arguments.append(arg_def)

        return cls(
            command,
            arguments=arguments,
            title=title,
            description=description,
        )

    @classmethod
    def parse_command(
        cls,
        command: Command[T],
        *,
        argv: list[str],
        render: typing.Callable | None = None,
        exit_with=None,
        color: bool = True,
        version: str | Arg | None = None,
        help: bool | Arg = True,
    ) -> tuple[Command[T], HasCommand[T]]:
        command_def = cls.collect(command)

        if render is None:  # pragma: no cover
            from cappa import argparse

            render = argparse.render

        parsed_command, parsed_args = render(
            command_def,
            argv,
            exit_with=exit_with,
            color=color,
            version=version,
            help=help,
        )
        result = command_def.map_result(command, parsed_args)
        return parsed_command, result

    def map_result(self, command: Command[T], parsed_args) -> T:
        kwargs = {}
        for arg in self.arguments:
            if arg.name not in parsed_args:
                continue

            value = parsed_args[arg.name]
            if isinstance(arg, Subcommands):
                value = arg.map_result(value)
            else:
                assert arg.parse
                value = arg.parse(value)

            kwargs[arg.name] = value

        return command.cmd_cls(**kwargs)


@dataclasses.dataclass
class Subcommands(typing.Generic[T]):
    name: str
    options: dict[str, CommandDefinition]
    required: bool
    help: str

    def map_result(self, parsed_args):
        option_name = parsed_args.pop("__name__")
        option = self.options[option_name]
        return option.map_result(option.command, parsed_args)
