from __future__ import annotations

import contextlib
import dataclasses
import sys
from collections.abc import Callable
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generator,
    Generic,
    Hashable,
    Iterable,
    Protocol,
    Sequence,
    TextIO,
    TypedDict,
    TypeVar,
    cast,
)

from type_lens.type_view import TypeView

from cappa.arg import Arg, FinalArg, Group
from cappa.class_inspect import fields as get_fields
from cappa.class_inspect import get_command, get_command_capable_object
from cappa.docstring import ClassHelpText
from cappa.help import HelpFormattable, HelpFormatter
from cappa.invoke.types import Resolved
from cappa.output import Exit, Output
from cappa.state import S, State
from cappa.subcommand import FinalSubcommand, Subcommand
from cappa.type_view import CallableView
from cappa.types import ParseResult
from cappa.typing import assert_type

if TYPE_CHECKING:
    from cappa.base import Backend, CappaCapable

T = TypeVar("T")


@dataclasses.dataclass(frozen=True)
class Alias:
    """Describe an alternate name for a subcommand.

    Arguments:
        name: The alternate name a user may type to invoke the subcommand.
        hidden: If `True`, the alias is accepted but omitted from help output and
            from shell completion. Useful for supporting old names without
            advertising them.
        deprecated: If supplied, invoking the subcommand via this alias will emit
            a deprecation warning. If `True`, a default message is used; a string
            value is used as the deprecation message verbatim.
    """

    name: str
    hidden: bool = False
    deprecated: bool | str = False

    @classmethod
    def coerce(cls, value: str | Alias) -> Alias:
        if isinstance(value, Alias):
            return value
        return cls(name=value)


class CommandArgs(TypedDict, total=False):
    cmd_cls: type
    arguments: list[Arg[Any] | Subcommand]
    name: str | None
    aliases: list[str | Alias]
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
        epilog: Optional text displayed after the argument list in the help output.
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
    arguments: Sequence[Arg[Any] | Subcommand | FinalDestructure[Any]] = (
        dataclasses.field(default_factory=lambda: [])
    )
    propagated_arguments: list[FinalArg[Any]] = dataclasses.field(
        default_factory=lambda: []
    )

    name: str | None = None
    aliases: list[str | Alias] = dataclasses.field(default_factory=lambda: [])
    help: str | None = None
    description: str | None = None
    epilog: str | None = None
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

    def resolved_aliases(self) -> list[Alias]:
        return [Alias.coerce(a) for a in self.aliases]

    def collect(
        self,
        propagated_arguments: list[FinalArg[Any]] | None = None,
        state: State[Any] | None = None,
    ) -> FinalCommand[T]:
        kwargs: CommandArgs = CommandArgs()

        help_text = ClassHelpText.collect(self.cmd_cls)

        if not self.help:
            kwargs["help"] = help_text.summary

        if not self.description:
            kwargs["description"] = help_text.body

        fields = get_fields(self.cmd_cls)
        function_view = CallableView.from_callable(self.cmd_cls, include_extras=True)

        propagated_arguments = propagated_arguments or []

        arguments: list[FinalArg[Any] | FinalDestructure[Any]] = []
        raw_subcommands: list[tuple[Subcommand, TypeView[Any] | None, str | None]] = []
        if self.arguments:
            param_by_name = {p.name: p for p in function_view.parameters}
            for arg in self.arguments:
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
                            default_short=self.default_short,
                            default_long=self.default_long,
                            fallback_help=arg_help,
                            state=state,
                        )
                    )
                elif isinstance(arg, FinalDestructure):
                    arguments.append(arg)
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
                    arg_defs = Arg.collect(
                        field,
                        param_view.type_view,
                        fallback_help=arg_help,
                        default_short=self.default_short,
                        default_long=self.default_long,
                        state=state,
                    )
                    arguments.extend(arg_defs)

        propagating_arguments = [
            *propagated_arguments,
            *(arg for arg in arguments if isinstance(arg, FinalArg) and arg.propagate),
        ]
        subcommands = [
            subcommand.normalize(
                type_view,
                field_name,
                help_formatter=self.help_formatter,
                propagated_arguments=propagating_arguments,
                state=state,
            )
            for subcommand, type_view, field_name in raw_subcommands
        ]

        check_group_identity([a for a in arguments if isinstance(a, FinalArg)])
        final_arguments: list[
            FinalArg[Any] | FinalSubcommand | FinalDestructure[Any]
        ] = [
            *arguments,
            *subcommands,
        ]

        return FinalCommand(
            cmd_cls=self.cmd_cls,
            arguments=final_arguments,
            propagated_arguments=propagated_arguments,
            name=self.name,
            aliases=self.aliases,
            help=kwargs.get("help", self.help),
            description=kwargs.get("description", self.description),
            epilog=self.epilog,
            invoke=self.invoke,
            hidden=self.hidden,
            default_short=self.default_short,
            default_long=self.default_long,
            deprecated=self.deprecated,
            help_formatter=self.help_formatter,
            _collected=self._collected,
        )


@dataclasses.dataclass
class FinalCommand(Command[T]):
    """Post-normalization form of :class:`Command` with narrowed field types.

    Produced exclusively by :meth:`Command.collect`.
    """

    arguments: Sequence[FinalArg[Any] | FinalSubcommand | FinalDestructure[Any]] = (  # pyright: ignore
        dataclasses.field(default_factory=list)
    )
    propagated_arguments: list[FinalArg[Any]] = dataclasses.field(  # pyright: ignore
        default_factory=list
    )

    @property
    def subcommand(self) -> FinalSubcommand | None:
        return next(
            (arg for arg in self.arguments if isinstance(arg, FinalSubcommand)),
            None,
        )

    @property
    def value_arguments(self) -> Iterable[FinalArg[Any]]:
        for arg in self.arguments:
            if isinstance(arg, FinalArg) and arg.has_value:
                yield arg

    @property
    def destructured_arguments(self) -> Iterable[FinalDestructure[Any]]:
        for arg in self.arguments:
            if isinstance(arg, FinalDestructure):
                yield arg

    @property
    def all_arguments(self) -> Iterable[FinalArg[Any] | FinalSubcommand]:
        for arg in self.arguments:
            if not isinstance(arg, FinalDestructure):
                yield arg
        for arg in self.propagated_arguments:
            yield arg

    @property
    def options(self) -> Iterable[FinalArg[Any]]:
        for arg in self.arguments:
            if isinstance(arg, FinalArg) and arg.is_option:
                yield arg

    @property
    def positional_arguments(
        self,
    ) -> Iterable[FinalArg[Any] | FinalSubcommand]:
        for arg in self.arguments:
            if (
                isinstance(arg, FinalArg) and not arg.short and not arg.long
            ) or isinstance(arg, FinalSubcommand):
                yield arg

    def add_meta_actions(
        self,
        help: FinalArg[bool] | None = None,
        version: FinalArg[str] | None = None,
        completion: FinalArg[bool] | None = None,
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
            if help and isinstance(arg, FinalSubcommand)
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

    def map_result(
        self,
        command: FinalCommand[T],
        prog: str,
        parsed_args: dict[str, Any],
        output: Output,
        state: State[Any] | None = None,
        input: TextIO | None = None,
    ) -> tuple[Resolved[T], dict[Hashable, Any]]:
        state = State.ensure(state)  # pyright: ignore

        kwargs: dict[str, Any] = {}
        for arg in self.value_arguments:
            kwargs[arg.field_name] = arg.map_result(
                prog, parsed_args, state=state, input=input
            )

        subcommand_deps: dict[Hashable, Any] = {}
        for destructure in self.destructured_arguments:
            fd_parsed = parsed_args.get(destructure.field_name, {})
            fd_resolved = destructure.map_result(
                prog, fd_parsed, output, state=state, input=input
            )
            kwargs[destructure.field_name] = fd_resolved

        subcommand = self.subcommand
        if subcommand:
            field_name = subcommand.field_name
            if field_name in parsed_args:
                value = parsed_args[field_name]
                value, subcommand_deps = subcommand.map_result(
                    prog, value, output=output, state=state
                )
                kwargs[field_name] = value

        def map_result(**kwargs: dict[str, Any]) -> T:
            with graceful_exit(command, prog, output):
                return command.cmd_cls(**kwargs)

        resolved = Resolved(map_result, kwargs=kwargs)
        key = cast(Hashable, command.cmd_cls)
        deps: dict[Hashable, Any] = {key: resolved, **subcommand_deps}
        return resolved, deps

    def parse_command(
        self,
        *,
        output: Output,
        backend: Backend,
        argv: list[str] | None = None,
        input: TextIO | None = None,
        state: State[S] | None = None,
    ) -> ParseResult[T, S]:
        if argv is None:  # pragma: no cover
            argv = sys.argv[1:]

        prog = self.real_name()
        result_state: State[S] = State.ensure(state)  # type: ignore

        with graceful_exit(self, prog, output):
            parser, parsed_command, parsed_args = backend(
                self, argv, output=output, prog=prog
            )
            prog = parser.prog
            result, implicit_deps = self.map_result(
                self, prog, parsed_args, state=state, input=input, output=output
            )

        return ParseResult(
            root_command=self,
            parsed_command=parsed_command,
            instance=result,
            implicit_deps=implicit_deps,
            output=output,
            state=result_state,
        )


H = TypeVar("H", covariant=True)


class HasCommand(Generic[H], Protocol):
    __cappa__: ClassVar[Command[Any]]


def check_group_identity(args: list[FinalArg[Any]]):
    group_identity: dict[str, Group] = {}

    for arg in args:
        identity = group_identity.get(arg.group.id)
        if identity and identity != arg.group:
            raise ValueError(
                f"Group details do not match among arguments: {arg.group.diff(identity)}."
            )

        group_identity[arg.group.id] = arg.group


@contextlib.contextmanager
def graceful_exit(
    command: FinalCommand[T], prog: str, output: Output
) -> Generator[None, None, None]:
    try:
        yield
    except BaseException as e:
        if isinstance(e, Exit):
            command = e.command or command
            prog = e.prog or prog

        help = command.help_formatter.long(command, prog)
        short_help = command.help_formatter.short(command, prog)

        if isinstance(e, ValueError):
            exc = Exit(str(e), code=2, prog=prog, command=command)
            output.exit(exc, help=help, short_help=short_help)
            raise exc

        if isinstance(e, Exit):
            output.exit(e, help=help, short_help=short_help)
            raise

        raise


from cappa.destructure import FinalDestructure  # noqa: E402
