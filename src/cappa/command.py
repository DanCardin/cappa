from __future__ import annotations

import dataclasses
import sys
from collections.abc import Callable
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    Iterable,
    Protocol,
    TextIO,
    TypedDict,
    TypeVar,
    cast,
)

from type_lens.type_view import TypeView

from cappa.arg import Arg, Group
from cappa.class_inspect import fields as get_fields
from cappa.class_inspect import get_command, get_command_capable_object
from cappa.default import Default
from cappa.docstring import ClassHelpText
from cappa.help import HelpFormattable, HelpFormatter, format_short_help
from cappa.output import Exit, Output
from cappa.state import S, State
from cappa.subcommand import Subcommand
from cappa.type_view import CallableView
from cappa.typing import assert_type

if TYPE_CHECKING:
    from cappa.base import Backend, CappaCapable

T = TypeVar("T")


class CommandArgs(TypedDict, total=False):
    cmd_cls: type
    arguments: list[Arg[Any] | Subcommand]
    name: str | None
    help: str | None
    description: str | None
    invoke: Callable[..., Any] | str | None

    hidden: bool
    default_short: bool
    default_long: bool


@dataclasses.dataclass
class Command(Generic[T]):
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
        default_long: If `True`, all arguments will be treated as though annotated
            with `Annotated[T, Arg(long=True)]`, unless otherwise annotated.
        deprecated: If supplied, the argument will be marked as deprecated. If given `True`,
            a default message will be generated, otherwise a supplied string will be
            used as the deprecation message.
    """

    cmd_cls: type[T]
    arguments: list[Arg[Any] | Subcommand] = dataclasses.field(
        default_factory=lambda: []
    )
    propagated_arguments: list[Arg[Any]] = dataclasses.field(default_factory=lambda: [])

    name: str | None = None
    help: str | None = None
    description: str | None = None
    invoke: Callable[..., Any] | str | None = None

    hidden: bool = False
    default_short: bool = False
    default_long: bool = False
    deprecated: bool | str = False

    help_formatter: HelpFormattable = HelpFormatter.default

    _collected: bool = False

    @classmethod
    def get(
        cls, obj: CappaCapable[T], help_formatter: HelpFormattable | None = None
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
            obj,  # pyright: ignore
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
        cls,
        command: Command[T],
        propagated_arguments: list[Arg[Any]] | None = None,
        state: State[Any] | None = None,
    ) -> Command[T]:
        kwargs: CommandArgs = CommandArgs()

        help_text = ClassHelpText.collect(command.cmd_cls)

        if not command.help:
            kwargs["help"] = help_text.summary

        if not command.description:
            kwargs["description"] = help_text.body

        fields = get_fields(command.cmd_cls)
        function_view = CallableView.from_callable(command.cmd_cls, include_extras=True)

        propagated_arguments = propagated_arguments or []

        arguments: list[Arg[Any]] = []
        raw_subcommands: list[tuple[Subcommand, TypeView[Any] | None, str | None]] = []
        if command.arguments:
            param_by_name = {p.name: p for p in function_view.parameters}
            for arg in command.arguments:
                arg_help = help_text.args.get(assert_type(arg.field_name, str))
                if isinstance(arg, Arg):
                    type_view = (
                        param_by_name[cast(str, arg.field_name)].type_view
                        if arg.field_name in param_by_name
                        else None
                    )
                    arguments.append(
                        arg.normalize(
                            type_view=type_view,
                            default_short=command.default_short,
                            default_long=command.default_long,
                            fallback_help=arg_help,
                            state=state,
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
                    arg_defs: list[Arg[Any]] = Arg.collect(
                        field,
                        param_view.type_view,
                        fallback_help=arg_help,
                        default_short=command.default_short,
                        default_long=command.default_long,
                        state=state,
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
                state=state,
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
        backend: Backend,
        argv: list[str] | None = None,
        input: TextIO | None = None,
        state: State[S] | None = None,
    ) -> tuple[Command[T], Command[T], T, State[S]]:
        if argv is None:  # pragma: no cover
            argv = sys.argv[1:]

        prog = command.real_name()
        result_state = State.ensure(state)  # pyright: ignore

        try:
            parser, parsed_command, parsed_args = backend(
                command, argv, output=output, prog=prog
            )
            prog = parser.prog
            result = command.map_result(
                command, prog, parsed_args, state=state, input=input
            )
        except BaseException as e:
            if isinstance(e, Exit):
                command = e.command or command
                prog = e.prog or prog

            help = command.help_formatter(command, prog)
            short_help = format_short_help(command, prog)

            if isinstance(e, ValueError):
                exc = Exit(str(e), code=2, prog=prog, command=command)
                output.exit(exc, help=help, short_help=short_help)
                raise exc

            if isinstance(e, Exit):
                output.exit(e, help=help, short_help=short_help)
                raise

            raise

        return command, parsed_command, result, result_state  # type: ignore

    def map_result(
        self,
        command: Command[T],
        prog: str,
        parsed_args: dict[str, Any],
        state: State[Any] | None = None,
        input: TextIO | None = None,
    ) -> T:
        state = State.ensure(state)  # pyright: ignore

        kwargs: dict[str, Any] = {}
        for arg in self.value_arguments:
            field_name = cast(str, arg.field_name)

            is_parsed = False
            if arg.field_name in parsed_args:
                value = parsed_args[field_name]
            else:
                assert isinstance(arg.default, Default), arg
                is_parsed, value = arg.default(state=state, input=input)

            if not is_parsed:
                assert arg.parse
                assert callable(arg.parse)

                try:
                    value = arg.parse(value)
                except Exception as e:
                    exception_reason = str(e)
                    raise Exit(
                        f"Invalid value for '{arg.names_str()}': {exception_reason}",
                        code=2,
                        prog=prog,
                    )

            kwargs[field_name] = value

        subcommand = self.subcommand
        if subcommand:
            field_name = cast(str, subcommand.field_name)
            if field_name in parsed_args:
                value = parsed_args[field_name]
                value = subcommand.map_result(prog, value, state=state)
                kwargs[field_name] = value

        return command.cmd_cls(**kwargs)

    @property
    def subcommand(self) -> Subcommand | None:
        return next(
            (arg for arg in self.arguments if isinstance(arg, Subcommand)), None
        )

    @property
    def value_arguments(self) -> Iterable[Arg[Any]]:
        for arg in self.arguments:
            if isinstance(arg, Arg) and arg.has_value:
                yield arg

    @property
    def all_arguments(self) -> Iterable[Arg[Any] | Subcommand]:
        for arg in self.arguments:
            yield arg

        for arg in self.propagated_arguments:
            yield arg

    @property
    def options(self) -> Iterable[Arg[Any]]:
        for arg in self.arguments:
            if isinstance(arg, Arg) and arg.is_option:
                yield arg

    @property
    def positional_arguments(self) -> Iterable[Arg[Any] | Subcommand]:
        for arg in self.arguments:
            if (
                isinstance(arg, Arg)
                and not arg.short
                and not arg.long
                and not arg.destructure
            ) or isinstance(arg, Subcommand):
                yield arg

    def add_meta_actions(
        self,
        help: Arg[bool] | None = None,
        version: Arg[str] | None = None,
        completion: Arg[bool] | None = None,
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


H = TypeVar("H", covariant=True)


class HasCommand(Generic[H], Protocol):
    __cappa__: ClassVar[Command[Any]]


def check_group_identity(args: list[Arg[Any]]):
    group_identity: dict[str, Group] = {}

    for arg in args:
        assert isinstance(arg.group, Group)

        name = arg.group.name
        identity = group_identity.get(name)
        if identity and identity != arg.group:
            raise ValueError(
                f"Group details between `{identity}` and `{arg.group}` must match"
            )

        assert isinstance(arg.group, Group)
        group_identity[name] = arg.group
