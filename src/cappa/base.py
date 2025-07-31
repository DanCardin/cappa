from __future__ import annotations

import dataclasses
import inspect
from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
    TextIO,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

from rich.theme import Theme
from typing_extensions import dataclass_transform

from cappa import argparse, parser
from cappa.class_inspect import detect
from cappa.command import Command
from cappa.help import (
    HelpFormattable,
    HelpFormatter,
    create_completion_arg,
    create_help_arg,
    create_version_arg,
)
from cappa.invoke import DepTypes, InvokeCallable, InvokeCallableSpec, resolve_callable
from cappa.output import Output
from cappa.state import S, State

if TYPE_CHECKING:
    from cappa.arg import Arg

T = TypeVar("T")
U = TypeVar("U")

CappaCapable = Union[InvokeCallable[T], Type[T], Command[T]]


class Backend(Protocol):
    def __call__(
        self,
        command: Command[T],
        argv: list[str],
        output: Output,
        prog: str,
        provide_completions: bool = False,
    ) -> tuple[Any, Command[T], dict[str, Any]]: ...  # pragma: no cover


def parse(
    obj: CappaCapable[T],
    *,
    argv: list[str] | None = None,
    input: TextIO | None = None,
    backend: Backend | None = None,
    color: bool = True,
    version: str | Arg[Any] | None = None,
    help: bool | Arg[Any] = True,
    completion: bool | Arg[Any] = True,
    theme: Theme | None = None,
    output: Output | None = None,
    help_formatter: HelpFormattable | None = None,
    state: State[Any] | None = None,
) -> T:
    """Parse the command, returning an instance of `obj`.

    In the event that a subcommand is selected, only the selected subcommand
    function is invoked.

    Arguments:
        obj: A class which can represent a CLI command chain.
        argv: Defaults to the process argv. This command is generally only
            necessary when testing.
        input: Defaults to the process stdin. This command is generally only
            necessary when testing.
        backend: A function used to perform the underlying parsing and return a raw
            parsed state. This defaults to the native cappa parser, but can be changed
            to the argparse parser at `cappa.argparse.backend`.
        color: Whether to output in color.
        version: If a string is supplied, adds a -v/--version flag which returns the
            given string as the version. If an `Arg` is supplied, uses the `name`/`short`/`long`/`help`
            fields to add a corresponding version argument. Note the `name` is assumed to **be**
            the CLI's version, e.x. `Arg('1.2.3', help="Prints the version")`.
        help: If `True` (default to True), adds a -h/--help flag. If an `Arg` is supplied,
            uses the `short`/`long`/`help` fields to add a corresponding help argument.
        completion: Enables completion when using the cappa `backend` option. If `True`
            (default to True), adds a --completion flag. An `Arg` can be supplied to customize
            the argument's behavior.
        theme: Optional rich theme to customized output formatting.
        output: Optional `Output` instance. A default `Output` will constructed if one is not provided.
            Note the `color` and `theme` arguments take precedence over manually constructed `Output`
            attributes.
        help_formatter: Override the default help formatter.
        state: Optional initial State object.
    """
    _, _, instance, _, _ = parse_command(
        obj=obj,
        argv=argv,
        input=input,
        backend=backend,
        color=color,
        version=version,
        help=help,
        completion=completion,
        theme=theme,
        output=output,
        help_formatter=help_formatter,
        state=state,
    )
    return instance


def invoke(
    obj: CappaCapable[T],
    *,
    deps: DepTypes = None,
    argv: list[str] | None = None,
    input: TextIO | None = None,
    backend: Backend | None = None,
    color: bool = True,
    version: str | Arg[Any] | None = None,
    help: bool | Arg[Any] = True,
    completion: bool | Arg[Any] = True,
    theme: Theme | None = None,
    output: Output | None = None,
    help_formatter: HelpFormattable | None = None,
    state: State[Any] | None = None,
):
    """Parse the command, and invoke the selected async command or subcommand.

    In the event that a subcommand is selected, only the selected subcommand
    function is invoked.

    Arguments:
        obj: A class which can represent a CLI command chain.
        deps: Optional extra depdnencies to load ahead of invoke processing. These
            deps are evaluated in order and unconditionally.
        argv: Defaults to the process argv. This command is generally only
            necessary when testing.
        input: Defaults to the process stdin. This command is generally only
            necessary when testing.
        backend: A function used to perform the underlying parsing and return a raw
            parsed state. This defaults to the native cappa parser, but can be changed
            to the argparse parser at `cappa.argparse.backend`.
        color: Whether to output in color.
        version: If a string is supplied, adds a -v/--version flag which returns the
            given string as the version. If an `Arg` is supplied, uses the `name`/`short`/`long`/`help`
            fields to add a corresponding version argument. Note the `name` is assumed to **be**
            the CLI's version, e.x. `Arg('1.2.3', help="Prints the version")`.
        help: If `True` (default to True), adds a -h/--help flag. If an `Arg` is supplied,
            uses the `short`/`long`/`help` fields to add a corresponding help argument.
        completion: Enables completion when using the cappa `backend` option. If `True`
            (default to True), adds a --completion flag. An `Arg` can be supplied to customize
            the argument's behavior.
        theme: Optional rich theme to customized output formatting.
        output: Optional `Output` instance. A default `Output` will constructed if one is not provided.
            Note the `color` and `theme` arguments take precedence over manually constructed `Output`
            attributes.
        help_formatter: Override the default help formatter.
        state: Optional initial State object.
    """
    command, parsed_command, instance, concrete_output, state = parse_command(
        obj=obj,
        argv=argv,
        input=input,
        backend=backend,
        color=color,
        version=version,
        help=help,
        completion=completion,
        theme=theme,
        output=output,
        help_formatter=help_formatter,
        state=state,
    )
    resolved, global_deps = resolve_callable(
        command,
        parsed_command,
        instance,
        output=concrete_output,
        state=state,
        deps=deps,
    )
    for dep in global_deps:
        with dep.get(output=concrete_output):
            pass

    return resolved.call(output=concrete_output)


async def invoke_async(
    obj: CappaCapable[T],
    *,
    deps: DepTypes = None,
    argv: list[str] | None = None,
    input: TextIO | None = None,
    backend: Backend | None = None,
    color: bool = True,
    version: str | Arg[str] | None = None,
    help: bool | Arg[bool] = True,
    completion: bool | Arg[bool] = True,
    theme: Theme | None = None,
    output: Output | None = None,
    help_formatter: HelpFormattable | None = None,
    state: State[Any] | None = None,
) -> Any:
    """Parse the command, and invoke the selected command or subcommand.

    In the event that a subcommand is selected, only the selected subcommand
    function is invoked.

    Arguments:
        obj: A class which can represent a CLI command chain.
        deps: Optional extra depdnencies to load ahead of invoke processing. These
            deps are evaluated in order and unconditionally.
        argv: Defaults to the process argv. This command is generally only
            necessary when testing.
        input: Defaults to the process stdin. This command is generally only
            necessary when testing.
        backend: A function used to perform the underlying parsing and return a raw
            parsed state. This defaults to the native cappa parser, but can be changed
            to the argparse parser at `cappa.argparse.backend`.
        color: Whether to output in color.
        version: If a string is supplied, adds a -v/--version flag which returns the
            given string as the version. If an `Arg` is supplied, uses the `name`/`short`/`long`/`help`
            fields to add a corresponding version argument. Note the `name` is assumed to **be**
            the CLI's version, e.x. `Arg('1.2.3', help="Prints the version")`.
        help: If `True` (default to True), adds a -h/--help flag. If an `Arg` is supplied,
            uses the `short`/`long`/`help` fields to add a corresponding help argument.
        completion: Enables completion when using the cappa `backend` option. If `True`
            (default to True), adds a --completion flag. An `Arg` can be supplied to customize
            the argument's behavior.
        theme: Optional rich theme to customized output formatting.
        output: Optional `Output` instance. A default `Output` will constructed if one is not provided.
            Note the `color` and `theme` arguments take precedence over manually constructed `Output`
            attributes.
        help_formatter: Override the default help formatter.
        state: Optional initial State object.
    """
    command, parsed_command, instance, concrete_output, state = parse_command(
        obj=obj,
        argv=argv,
        input=input,
        backend=backend,
        color=color,
        version=version,
        help=help,
        completion=completion,
        theme=theme,
        output=output,
        help_formatter=help_formatter,
        state=state,
    )
    resolved, global_deps = resolve_callable(
        command,
        parsed_command,
        instance,
        output=concrete_output,
        state=state,
        deps=deps,
    )
    for dep in global_deps:
        async with dep.get_async(output=concrete_output):
            pass

    async with resolved.get_async(output=concrete_output) as value:
        return value


def parse_command(
    obj: CappaCapable[T],
    *,
    argv: list[str] | None = None,
    input: TextIO | None = None,
    backend: Backend | None = None,
    color: bool = True,
    version: str | Arg[str] | None = None,
    help: bool | Arg[bool] = True,
    completion: bool | Arg[bool] = True,
    theme: Theme | None = None,
    output: Output | None = None,
    help_formatter: HelpFormattable | None = None,
    state: State[S] | None = None,
) -> tuple[Command[T], Command[T], T, Output, State[Any]]:
    concrete_backend = _coalesce_backend(backend)
    concrete_output = _coalesce_output(output, theme, color)
    concrete_state: State[S] = State.ensure(state)  # type: ignore

    command: Command[T] = collect(
        obj,
        help=help,
        version=version,
        completion=completion,
        backend=concrete_backend,
        help_formatter=help_formatter,
        state=concrete_state,
    )
    command, parsed_command, instance, state = Command.parse_command(  # pyright: ignore
        command,
        argv=argv,
        input=input,
        backend=concrete_backend,
        output=concrete_output,
        state=concrete_state,
    )
    return command, parsed_command, instance, concrete_output, concrete_state  # pyright: ignore


class FuncOrClassDecorator(Protocol):
    @overload
    def __call__(self, x: type[T], /) -> type[T]: ...
    @overload
    def __call__(self, x: T, /) -> T: ...


@overload
def command(
    _cls: type[T],
    *,
    name: str | None = None,
    help: str | None = None,
    description: str | None = None,
    invoke: InvokeCallableSpec[Any] | None = None,
    hidden: bool = False,
    default_short: bool = False,
    default_long: bool = False,
    deprecated: bool = False,
    help_formatter: HelpFormattable = HelpFormatter.default,
) -> type[T]: ...
@overload
def command(
    *,
    name: str | None = None,
    help: str | None = None,
    description: str | None = None,
    invoke: InvokeCallableSpec[Any] | None = None,
    hidden: bool = False,
    default_short: bool = False,
    default_long: bool = False,
    deprecated: bool = False,
    help_formatter: HelpFormattable = HelpFormatter.default,
) -> FuncOrClassDecorator: ...
@overload
def command(
    _cls: T,
    *,
    name: str | None = None,
    help: str | None = None,
    description: str | None = None,
    invoke: InvokeCallableSpec[Any] | None = None,
    hidden: bool = False,
    default_short: bool = False,
    default_long: bool = False,
    deprecated: bool = False,
    help_formatter: HelpFormattable = HelpFormatter.default,
) -> T: ...


@dataclass_transform()  # type: ignore[misc]
def command(
    _cls: type[T] | T | None = None,
    *,
    name: str | None = None,
    help: str | None = None,
    description: str | None = None,
    invoke: InvokeCallableSpec[Any] | None = None,
    hidden: bool = False,
    default_short: bool = False,
    default_long: bool = False,
    deprecated: bool = False,
    help_formatter: HelpFormattable = HelpFormatter.default,
) -> type[T] | T | FuncOrClassDecorator:
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
        hidden: If `True`, the command will not be included in the help output.
            This option is only relevant to subcommands.
        default_short: If `True`, all arguments will be treated as though annotated
            with `Annotated[T, Arg(short=True)]`, unless otherwise annotated.
        default_long: If `True`, all arguments will be treated as though annotated
            with `Annotated[T, Arg(long=True)]`, unless otherwise annotated.
        deprecated: If supplied, the argument will be marked as deprecated. If given `True`,
            a default message will be generated, otherwise a supplied string will be
            used as the deprecation message.
        help_formatter: Override the default help formatter.
    """

    def wrapper(_decorated_cls: U) -> U:
        if inspect.isclass(_decorated_cls) and not detect(_decorated_cls):
            _decorated_cls = dataclasses.dataclass(_decorated_cls)  # type: ignore

        command: Command[T] = Command.get(_decorated_cls)  # type: ignore
        instance = dataclasses.replace(
            command,
            invoke=invoke,
            name=name,
            help=help,
            description=description,
            hidden=hidden,
            default_short=default_short,
            default_long=default_long,
            deprecated=deprecated,
            help_formatter=help_formatter,
        )
        _decorated_cls.__cappa__ = instance  # type: ignore

        # Functions (and in particular class methods, must return a function object in order
        # to be attached as methods) cannot be nested, so we can just directly return it.
        if inspect.isfunction(_decorated_cls):
            return cast(U, _decorated_cls)

        # Whereas classes will **generally** be the **exact** object as `_decorated_cls` was,
        # except in the case of dynamically generated subclasses used for detecting methods.
        return instance.cmd_cls  # type: ignore

    if _cls is not None:
        return wrapper(_cls)
    return wrapper


def collect(
    obj: CappaCapable[T],
    *,
    backend: Backend | None = None,
    version: str | Arg[str] | None = None,
    help: bool | Arg[bool] = True,
    completion: bool | Arg[bool] = True,
    help_formatter: HelpFormattable | None = None,
    state: State[Any] | None = None,
) -> Command[T]:
    """Retrieve the `Command` object from a cappa-capable source class.

    Arguments:
        obj: A class which can represent a CLI command chain.
        backend: A function used to perform the underlying parsing and return a raw
            parsed state. This defaults to constructing built-in function using argparse.
        version: If a string is supplied, adds a -v/--version flag which returns the
            given string as the version. If an `Arg` is supplied, uses the `name`/`short`/`long`/`help`
            fields to add a corresponding version argument. Note the `name` is assumed to **be**
            the CLI's version, e.x. `Arg('1.2.3', help="Prints the version")`.
        help: If `True` (default to True), adds a -h/--help flag. If an `Arg` is supplied,
            uses the `short`/`long`/`help` fields to add a corresponding help argument.
        completion: Enables completion when using the cappa `backend` option. If `True`
            (default to True), adds a --completion flag. An `Arg` can be supplied to customize
            the argument's behavior.
        color: Whether to output in color.
        help_formatter: Override the default help formatter.
        state: Optional initial State object.
    """
    state = State.ensure(state)  # pyright: ignore

    command: Command[T] = Command.get(obj, help_formatter=help_formatter)  # pyright: ignore
    command = Command.collect(command, state=state)  # pyright: ignore

    concrete_backend = _coalesce_backend(backend)
    if concrete_backend is argparse.backend:  # pyright: ignore
        completion = False

    help_arg = create_help_arg(help)
    version_arg = create_version_arg(version)
    completion_arg = create_completion_arg(completion)

    return command.add_meta_actions(
        help=help_arg, version=version_arg, completion=completion_arg
    )


def _coalesce_backend(backend: Backend | None = None) -> Backend:
    if backend is None:  # pragma: no cover
        return parser.backend
    return backend


def _coalesce_output(
    output: Output | None = None, theme: Theme | None = None, color: bool = True
):
    if output is None:
        output = Output()

    output.theme(theme)

    if not color:
        output.color(False)

    return output
