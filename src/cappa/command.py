from __future__ import annotations

import dataclasses
import typing
from collections.abc import Callable

import docstring_parser
from typing_extensions import Self, get_type_hints

from cappa import class_inspect
from cappa.arg import Arg
from cappa.subcommand import Subcommand, Subcommands
from cappa.typing import assert_not_missing

T = typing.TypeVar("T")


class CommandArgs(typing.TypedDict, total=False):
    cmd_cls: type
    arguments: list[Arg | Subcommands]
    name: str | None
    help: str | None
    description: str | None
    invoke: Callable | str | None


@dataclasses.dataclass
class Command(typing.Generic[T]):
    """Register a cappa CLI command/subcomment.

    Args:
        cmd_cls: The class representing the command/subcommand
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
            function to invoke. The value can **either** be a callable object or
            a string. When the value is a string it will be interpreted as
            `module.submodule.function`; the module will be dynamically imported,
            and the referenced function invoked.
    """

    cmd_cls: typing.Type[T]
    arguments: list[Arg | Subcommands] = dataclasses.field(default_factory=list)
    name: str | None = None
    help: str | None = None
    description: str | None = None
    invoke: Callable | str | None = None

    @classmethod
    def wrap(
        cls,
        *,
        name: str | None = None,
        help: str | None = None,
        description: str | None = None,
        invoke: Callable | str | None = None,
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
            instance = cls(
                cmd_cls=_decorated_cls,
                invoke=invoke,
                name=name,
                help=help,
                description=description,
            )
            _decorated_cls.__cappa__ = instance
            return _decorated_cls

        return wrapper

    @classmethod
    def get(cls, obj: typing.Type[T]) -> Self:
        if isinstance(obj, cls):
            return obj

        return getattr(obj, "__cappa__", cls(obj))

    def real_name(self) -> str:
        if self.name is not None:
            return self.name

        cls_name = self.cmd_cls.__name__
        import re

        return re.sub(r"(?<!^)(?=[A-Z])", "-", cls_name).lower()

    @classmethod
    def collect(cls, command: Command):
        kwargs: CommandArgs = {}
        arg_help_map = {}

        if not (command.help and command.description):
            parsed_help = docstring_parser.parse(command.cmd_cls.__doc__ or "")
            for param in parsed_help.params:
                arg_help_map[param.arg_name] = param.description

            if not command.help:
                kwargs["help"] = parsed_help.short_description

            if not command.description:
                kwargs["description"] = parsed_help.long_description

        if not command.arguments:
            command_cls = type(command)
            fields = class_inspect.fields(command.cmd_cls)
            type_hints = get_type_hints(command.cmd_cls, include_extras=True)

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

            kwargs["arguments"] = arguments

        return dataclasses.replace(command, **kwargs)

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
    ) -> tuple[Command[T], T]:
        command = cls.collect(command)

        if render is None:  # pragma: no cover
            from cappa import argparse

            render = argparse.render

        parsed_command, parsed_args = render(
            command,
            argv,
            exit_with=exit_with,
            color=color,
            version=version,
            help=help,
        )
        result = command.map_result(command, parsed_args)
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


H = typing.TypeVar("H", covariant=True)


class HasCommand(typing.Generic[H], typing.Protocol):
    __cappa__: typing.ClassVar[Command]
