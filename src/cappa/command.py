from __future__ import annotations

import dataclasses
import sys
import typing
from collections.abc import Callable

from type_lens.type_view import TypeView

from cappa.arg import Arg, Group
from cappa.class_inspect import fields as get_fields
from cappa.class_inspect import get_command, get_command_capable_object
from cappa.docstring import ClassHelpText
from cappa.env import Env
from cappa.help import HelpFormatable, HelpFormatter, format_short_help
from cappa.output import Exit, Output, prompt_types
from cappa.subcommand import Subcommand
from cappa.type_view import CallableView, Empty
from cappa.typing import assert_type

T = typing.TypeVar("T")


class CommandArgs(typing.TypedDict, total=False):
    cmd_cls: type
    arguments: list[Arg | Subcommand]
    name: str | None
    help: str | None
    description: str | None
    invoke: Callable | str | None

    hidden: bool
    default_short: bool
    default_long: bool


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
        hidden: If `True`, the command will not be included in the help output.
            This option is only relevant to subcommands.
        default_short: If `True`, all arguments will be treated as though annotated
            with `Annotated[T, Arg(short=True)]`, unless otherwise annotated.
        default_true: If `True`, all arguments will be treated as though annotated
            with `Annotated[T, Arg(long=True)]`, unless otherwise annotated.
        deprecated: If supplied, the argument will be marked as deprecated. If given `True`,
            a default message will be generated, otherwise a supplied string will be
            used as the deprecation message.
    """

    cmd_cls: type[T]
    arguments: list[Arg | Subcommand] = dataclasses.field(default_factory=list)
    propagated_arguments: list[Arg] = dataclasses.field(default_factory=list)

    name: str | None = None
    help: str | None = None
    description: str | None = None
    invoke: Callable | str | None = None

    hidden: bool = False
    default_short: bool = False
    default_long: bool = False
    deprecated: bool | str = False

    help_formatter: HelpFormatable = HelpFormatter.default

    _collected: bool = False

    @classmethod
    def get(
        cls, obj: type[T] | Command[T], help_formatter: HelpFormatable | None = None
    ) -> Command[T]:
        help_formatter = help_formatter or HelpFormatter.default

        instance = None
        if isinstance(obj, cls):
            instance = obj
        else:
            obj = get_command_capable_object(obj)
            instance = get_command(obj)

        if instance:
            return dataclasses.replace(instance, help_formatter=help_formatter)

        assert not isinstance(obj, Command)
        return cls(
            obj,
            help_formatter=help_formatter,
        )

    def real_name(self) -> str:
        if self.name is not None:
            return self.name

        import re

        cls_name = self.cmd_cls.__name__
        return re.sub(r"(?<!^)(?=[A-Z])", "-", cls_name).lower()

    @classmethod
    def collect(
        cls, command: Command[T], propagated_arguments: list[Arg] | None = None
    ) -> Command[T]:
        kwargs: CommandArgs = {}

        help_text = ClassHelpText.collect(command.cmd_cls)

        if not command.help:
            kwargs["help"] = help_text.summary

        if not command.description:
            kwargs["description"] = help_text.body

        fields = get_fields(command.cmd_cls)
        function_view = CallableView.from_callable(command.cmd_cls, include_extras=True)

        propagated_arguments = propagated_arguments or []

        arguments = []
        raw_subcommands: list[tuple[Subcommand, TypeView | None, str | None]] = []
        if command.arguments:
            param_by_name = {p.name: p for p in function_view.parameters}
            for arg in command.arguments:
                arg_help = help_text.args.get(assert_type(arg.field_name, str))
                if isinstance(arg, Arg):
                    type_view = (
                        param_by_name[typing.cast(str, arg.field_name)].type_view
                        if arg.field_name in param_by_name
                        else None
                    )
                    arguments.append(
                        arg.normalize(
                            type_view=type_view,
                            default_short=command.default_short,
                            default_long=command.default_long,
                            fallback_help=arg_help,
                        )
                    )
                else:
                    raw_subcommands.append((arg, None, None))

        else:
            for field, param_view in zip(fields, function_view.parameters):
                arg_help = help_text.args.get(param_view.name)

                maybe_subcommand = Subcommand.detect(
                    field,
                    param_view.type_view,
                )
                if maybe_subcommand:
                    raw_subcommands.append(
                        (
                            maybe_subcommand,
                            param_view.type_view,
                            field.name,
                        )
                    )
                else:
                    arg_defs: list[Arg] = Arg.collect(
                        field,
                        param_view.type_view,
                        fallback_help=arg_help,
                        default_short=command.default_short,
                        default_long=command.default_long,
                    )
                    arguments.extend(arg_defs)

        propagating_arguments = [
            *propagated_arguments,
            *(arg for arg in arguments if arg.propagate),
        ]
        subcommands = [
            subcommand.normalize(
                type_view,
                field_name,
                help_formatter=command.help_formatter,
                propagated_arguments=propagating_arguments,
            )
            for subcommand, type_view, field_name in raw_subcommands
        ]

        check_group_identity(arguments)
        kwargs["arguments"] = [*arguments, *subcommands]

        return dataclasses.replace(
            command,
            **kwargs,
            propagated_arguments=propagated_arguments,
        )

    @classmethod
    def parse_command(
        cls,
        command: Command[T],
        *,
        output: Output,
        backend: typing.Callable,
        argv: list[str] | None = None,
    ) -> tuple[Command, Command[T], T]:
        if argv is None:  # pragma: no cover
            argv = sys.argv[1:]

        prog = command.real_name()
        try:
            parser, parsed_command, parsed_args = backend(
                command, argv, output=output, prog=prog
            )
            prog = parser.prog
            result = command.map_result(command, prog, parsed_args)
        except Exit as e:
            command = e.command or command
            prog = e.prog or prog
            output.exit(
                e,
                help=command.help_formatter(command, prog),
                short_help=format_short_help(command, prog),
            )
            raise

        return command, parsed_command, result

    def map_result(self, command: Command[T], prog: str, parsed_args) -> T:
        kwargs = {}
        for arg in self.value_arguments():
            is_subcommand = isinstance(arg, Subcommand)
            parsed_arg = arg.field_name in parsed_args
            if not parsed_arg:
                if is_subcommand:
                    continue

                assert arg.default is not Empty, arg
                value = arg.default

            else:
                value = parsed_args[arg.field_name]

            if isinstance(value, (Env, *prompt_types)):
                value = value()
                parsed_arg = True

            if is_subcommand:
                value = arg.map_result(prog, value)
            else:
                assert arg.parse
                assert callable(arg.parse)

                if parsed_arg:
                    try:
                        value = arg.parse(value)
                    except Exception as e:
                        exception_reason = str(e)
                        raise Exit(
                            f"Invalid value for '{arg.names_str()}': {exception_reason}",
                            code=2,
                            prog=prog,
                        )

            kwargs[arg.field_name] = value

        return command.cmd_cls(**kwargs)

    def value_arguments(self):
        for arg in self.arguments:
            if isinstance(arg, Arg) and not arg.has_value:
                continue

            yield arg

    @property
    def all_arguments(self) -> typing.Iterable[Arg | Subcommand]:
        for arg in self.arguments:
            yield arg

        for arg in self.propagated_arguments:
            yield arg

    @property
    def options(self) -> typing.Iterable[Arg]:
        for arg in self.arguments:
            if isinstance(arg, Arg) and arg.is_option:
                yield arg

    @property
    def positional_arguments(self) -> typing.Iterable[Arg | Subcommand]:
        for arg in self.arguments:
            if (
                isinstance(arg, Arg)
                and not arg.short
                and not arg.long
                and not arg.destructured
            ) or isinstance(arg, Subcommand):
                yield arg

    def add_meta_actions(
        self,
        help: Arg | None = None,
        version: Arg | None = None,
        completion: Arg | None = None,
    ):
        if self._collected:
            return self

        arguments = [
            dataclasses.replace(
                arg,
                options={
                    name: option.add_meta_actions(help)
                    for name, option in arg.options.items()
                },
            )
            if help and isinstance(arg, Subcommand)
            else arg
            for arg in self.arguments
        ]

        if help:
            arguments.append(help)
        if version:
            arguments.append(version)
        if completion:
            arguments.append(completion)
        return dataclasses.replace(self, arguments=arguments, _collected=True)


H = typing.TypeVar("H", covariant=True)


class HasCommand(typing.Generic[H], typing.Protocol):
    __cappa__: typing.ClassVar[Command]


def check_group_identity(args: list[Arg]):
    group_identity: dict[str, Group] = {}

    for arg in args:
        assert isinstance(arg.group, Group)

        name = typing.cast(str, arg.group.name)
        identity = group_identity.get(name)
        if identity and identity != arg.group:
            raise ValueError(
                f"Group details between `{identity}` and `{arg.group}` must match"
            )

        assert isinstance(arg.group, Group)
        group_identity[name] = arg.group
