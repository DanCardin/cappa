from __future__ import annotations

import dataclasses
import inspect
import typing
from collections.abc import Callable

import docstring_parser
from typing_extensions import Self, get_type_hints

from cappa import class_inspect
from cappa.arg import Arg, ArgAction
from cappa.env import Env
from cappa.output import Exit, Output, prompt_types
from cappa.subcommand import Subcommand

T = typing.TypeVar("T")


class CommandArgs(typing.TypedDict, total=False):
    cmd_cls: type
    arguments: list[Arg | Subcommand]
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
    arguments: list[Arg | Subcommand] = dataclasses.field(default_factory=list)
    name: str | None = None
    help: str | None = None
    description: str | None = None
    invoke: Callable | str | None = None

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
            doc = get_doc(command.cmd_cls)
            parsed_help = docstring_parser.parse(doc)
            for param in parsed_help.params:
                arg_help_map[param.arg_name] = param.description

            if not command.help:
                kwargs["help"] = parsed_help.short_description

            if not command.description:
                kwargs["description"] = parsed_help.long_description

        if command.arguments:
            arguments: list[Arg | Subcommand] = [
                a.normalize() for a in command.arguments
            ]
        else:
            fields = class_inspect.fields(command.cmd_cls)
            type_hints = get_type_hints(command.cmd_cls, include_extras=True)

            arguments = []

            for field in fields:
                type_hint = type_hints[field.name]

                maybe_subcommand = Subcommand.collect(field, type_hint)
                if maybe_subcommand:
                    arguments.append(maybe_subcommand)
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
        output: Output,
        backend: typing.Callable | None = None,
        color: bool = True,
        version: str | Arg | None = None,
        help: bool | Arg = True,
        completion: bool | Arg = True,
    ) -> tuple[Command, Command[T], T]:
        command = cls.collect(command)

        if backend is None:  # pragma: no cover
            from cappa import argparse

            backend = argparse.backend

        try:
            _, parsed_command, parsed_args = backend(
                command,
                argv,
                color=color,
                version=version,
                help=help,
                completion=completion,
            )
            result = command.map_result(command, parsed_args)
        except Exit as e:
            output.exit(e)
            raise

        return command, parsed_command, result

    def map_result(self, command: Command[T], parsed_args) -> T:
        kwargs = {}
        for arg in self.value_arguments():
            is_subcommand = isinstance(arg, Subcommand)
            if arg.name not in parsed_args:
                # if arg.required:
                #     raise Exit(
                #         f"The following arguments are required: {arg.names_str()}",
                #         code=1,
                #     )

                if is_subcommand:
                    continue

                value = arg.default
            else:
                value = parsed_args[arg.name]

            if isinstance(value, Env):
                value = value.evaluate()
            if isinstance(value, prompt_types):
                value = value()

            if isinstance(arg, Subcommand):
                value = arg.map_result(value)
            else:
                assert arg.parse

                try:
                    value = arg.parse(value)
                except Exception as e:
                    exception_reason = str(e)
                    raise Exit(
                        f"Invalid value for '{arg.names_str()}' with value '{value}': {exception_reason}",
                        code=2,
                    )

            kwargs[arg.name] = value

        return command.cmd_cls(**kwargs)

    def value_arguments(self):
        for arg in self.arguments:
            if isinstance(arg, Arg):
                if arg.action in ArgAction.value_actions():
                    continue

            yield arg

    def add_meta_actions(
        self,
        help: Arg | None = None,
        version: Arg | None = None,
        completion: Arg | None = None,
    ):
        if help:
            for arg in self.arguments:
                if isinstance(arg, Subcommand):
                    for option in arg.options.values():
                        option.add_meta_actions(help)

            self.arguments.append(help)
        if version:
            self.arguments.append(version)
        if completion:
            self.arguments.append(completion)
        return self


H = typing.TypeVar("H", covariant=True)


class HasCommand(typing.Generic[H], typing.Protocol):
    __cappa__: typing.ClassVar[Command]


def get_doc(cls):
    """Lifted from dataclasses source."""
    doc = cls.__doc__ or ""

    # Dataclasses will set the doc attribute to the below value if there was no
    # explicit docstring. This is just annoying for us, so we treat that as though
    # there wasn't one.
    try:
        # In some cases fetching a signature is not possible.
        # But, we surely should not fail in this case.
        text_sig = str(inspect.signature(cls)).replace(" -> None", "")
    except (TypeError, ValueError):  # pragma: no cover
        text_sig = ""

    dataclasses_docstring = cls.__name__ + text_sig

    if doc == dataclasses_docstring:
        return ""
    return doc
