from __future__ import annotations

import dataclasses
import typing

import docstring_parser

from cappa.arg import Subcommand
from cappa.arg_def import ArgDefinition
from cappa.command import HasCommand
from cappa.invoke import invoke
from cappa.typing import assert_not_missing

if typing.TYPE_CHECKING:
    from cappa.command import Command

T = typing.TypeVar("T")


@dataclasses.dataclass
class CommandDefinition(typing.Generic[T]):
    command: Command[T]
    arguments: list[ArgDefinition[T] | Subcommands]

    title: str | None = None
    description: str | None = None

    @classmethod
    def collect(cls, command: Command):
        command_cls = type(command)
        fields = dataclasses.fields(command.cls)
        type_hints = typing.get_type_hints(command.cls, include_extras=True)

        title = None
        description = command.help
        arg_help_map = {}
        if not command.help:
            parsed_help = docstring_parser.parse(command.cls.__doc__ or "")
            title = parsed_help.short_description
            if description is None:
                description = parsed_help.long_description

            arg_help_map = {
                param.arg_name: param.description for param in parsed_help.params
            }

        arguments: list[ArgDefinition | Subcommands] = []

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
                arg_def: ArgDefinition | None = ArgDefinition.collect(
                    field, type_hint, help=arg_help
                )
                if arg_def:
                    arguments.append(arg_def)

        return cls(
            command,
            arguments=arguments,
            title=title,
            description=description,
        )

    @classmethod
    def parse(
        cls,
        command: Command[T],
        *,
        argv: list[str],
        render: typing.Callable | None = None,
        exit_with=None,
    ) -> T:
        _, instance = cls.parse_command(
            command, argv=argv, render=render, exit_with=exit_with
        )
        return instance  # type: ignore

    @classmethod
    def parse_command(
        cls,
        command: Command[T],
        *,
        argv: list[str],
        render: typing.Callable | None = None,
        exit_with=None,
    ) -> tuple[Command[T], HasCommand[T]]:
        command_def = cls.collect(command)

        if render is None:
            from cappa import argparse

            render = argparse.render

        parsed_command, parsed_args = render(command_def, argv, exit_with=exit_with)
        result = command_def.map_result(command, parsed_args)
        return parsed_command, result

    def map_result(self, command: Command[T], parsed_args) -> T:
        kwargs = {}
        for arg_def in self.arguments:
            if arg_def.name not in parsed_args:
                continue

            value = parsed_args[arg_def.name]

            if isinstance(arg_def, Subcommands):
                value = arg_def.map_result(value)
            else:
                if arg_def.map_result:
                    value = arg_def.map_result(value)

            kwargs[arg_def.name] = value

        return command.cls(**kwargs)

    @classmethod
    def invoke(
        cls,
        command: Command[T],
        *,
        argv: list[str],
        render: typing.Callable | None = None,
        exit_with=None,
    ):
        if not command.invoke:
            raise ValueError("no invoke")

        parsed_command, instance = cls.parse_command(
            command, argv=argv, render=render, exit_with=exit_with
        )
        return invoke(parsed_command, instance)  # type: ignore


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
