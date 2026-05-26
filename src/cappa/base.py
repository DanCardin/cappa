from __future__ import annotations

import contextlib
import dataclasses
import inspect
from typing import (
    TYPE_CHECKING,
    Any,
    Hashable,
    TextIO,
    cast,
    overload,
)

from rich.theme import Theme
from typing_extensions import dataclass_transform

from cappa import argparse, parser
from cappa.class_inspect import detect
from cappa.command import Alias, Command, FinalCommand
from cappa.help import HelpFormattable, HelpFormatter
from cappa.invoke.base import resolve_callable
from cappa.invoke.types import DepTypes, InvokeCallableSpec
from cappa.output import Output
from cappa.state import S, State
from cappa.types import Backend, CappaCapable, FuncOrClassDecorator, ParseResult, T, U

if TYPE_CHECKING:
    from cappa.arg import Arg, FinalArg


def create_version_arg(
    version: str | Arg[Any] | None = None,
) -> FinalArg[Any] | None:
    from dataclasses import replace

    from cappa.arg import Arg, ArgAction, Empty, Group

    if not version:
        return None

    if isinstance(version, str):
        version = Arg(
            value_name=version,
            short=["-v"],
            long=["--version"],
            help="Show the version and exit.",
            group=Group(1, "Help", section=2),
            action=ArgAction.version,
        )

    if version.value_name is Empty:
        raise ValueError(
            "Expected explicit version `Arg` to supply version number as its name, like `Arg('1.2.3', ...)`"
        )

    if version.long is True:
        version = replace(version, long="--version")

    return version.normalize(
        action=ArgAction.version, field_name="version", default=None
    )


def create_help_arg(help: bool | Arg[bool] | None = True) -> FinalArg[bool] | None:
    from cappa.arg import Arg, ArgAction, Group

    if not help:
        return None

    if isinstance(help, bool):
        help = Arg(
            short=["-h"],
            long=["--help"],
            help="Show this message and exit.",
            group=Group(0, "Help", section=2),
            action=ArgAction.help,
        )

    return help.normalize(action=ArgAction.help, field_name="help", default=None)


def create_completion_arg(
    completion: bool | Arg[bool] = True,
) -> FinalArg[bool] | None:
    from cappa.arg import Arg, ArgAction, Group

    if not completion:
        return None

    if isinstance(completion, bool):
        completion = Arg(
            long=["--completion"],
            choices=["generate", "complete"],
            group=Group(2, "Help", section=2),
            help="Use `--completion generate` to print shell-specific completion source.",
            action=ArgAction.completion,
        )

    return completion.normalize(
        field_name="completion",
        action=ArgAction.completion,
        default=None,
    )


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
    exit_stack: contextlib.ExitStack | None = None,
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
        exit_stack: Optional ExitStack to use for managing context managers. If provided,
            the caller is responsible for closing the stack, allowing context to exceed the
            function call. If not provided, contexts are not entered (parse does not manage
            contexts by default).
    """
    parse_result = parse_command(
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
    if exit_stack is not None:
        return exit_stack.enter_context(
            parse_result.instance.get(output=parse_result.output, managed=True)
        )
    return parse_result.instance.call(output=parse_result.output, managed=False)


async def parse_async(
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
    exit_stack: contextlib.AsyncExitStack | None = None,
) -> T:
    """Parse the command asynchronously, returning an instance of `obj`.

    This is the async version of `parse()`, necessary when using async parse functions.

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
        exit_stack: Optional AsyncExitStack to use for managing async context managers.
            If provided, the caller is responsible for closing the stack, allowing context
            to exceed the function call. If not provided, contexts are not entered (parse does
            not manage contexts by default).
    """
    parse_result = parse_command(
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
    if exit_stack is not None:
        return await exit_stack.enter_async_context(
            parse_result.instance.get_async(output=parse_result.output, managed=True)
        )
    return await parse_result.instance.call_async(
        output=parse_result.output, managed=False
    )


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
    exit_stack: contextlib.ExitStack | None = None,
) -> Any:
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
        exit_stack: Optional ExitStack to use for managing context managers. If provided,
            the caller is responsible for closing the stack, allowing context to exceed the
            function call. If not provided, a new stack is created and automatically closed.
    """
    parse_result = parse_command(
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

    def _invoke_with_stack(stack: contextlib.ExitStack):
        instance = stack.enter_context(
            parse_result.instance.get(output=parse_result.output)
        )

        # Resolve all implicit deps
        resolved_implicit_deps: dict[Hashable, Any] = {}
        for key, resolved_dep in parse_result.implicit_deps.items():
            resolved_implicit_deps[key] = stack.enter_context(
                resolved_dep.get(output=parse_result.output)
            )

        resolved, global_deps = resolve_callable(
            parse_result.root_command,
            parse_result.parsed_command,
            instance,
            implicit_deps=resolved_implicit_deps,
            output=parse_result.output,
            state=parse_result.state,
            deps=deps,
        )
        for dep in global_deps:
            stack.enter_context(dep.get(output=parse_result.output))

        return stack.enter_context(resolved.get(output=parse_result.output))

    if exit_stack is not None:
        return _invoke_with_stack(exit_stack)

    with contextlib.ExitStack() as stack:
        return _invoke_with_stack(stack)


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
    exit_stack: contextlib.AsyncExitStack | None = None,
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
        exit_stack: Optional AsyncExitStack to use for managing async context managers.
            If provided, the caller is responsible for closing the stack, allowing context to
            exceed the function call. If not provided, a new stack is created and automatically closed.
    """
    parse_result = parse_command(
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

    async def _invoke_async_with_stack(stack: contextlib.AsyncExitStack):
        instance = await stack.enter_async_context(
            parse_result.instance.get_async(output=parse_result.output)
        )

        # Resolve all implicit deps
        resolved_implicit_deps: dict[Hashable, Any] = {}
        for key, resolved_dep in parse_result.implicit_deps.items():
            resolved_implicit_deps[key] = await stack.enter_async_context(
                resolved_dep.get_async(output=parse_result.output)
            )

        resolved, global_deps = resolve_callable(
            parse_result.root_command,
            parse_result.parsed_command,
            instance,
            implicit_deps=resolved_implicit_deps,
            output=parse_result.output,
            state=parse_result.state,
            deps=deps,
        )
        for dep in global_deps:
            await stack.enter_async_context(dep.get_async(output=parse_result.output))

        return await stack.enter_async_context(
            resolved.get_async(output=parse_result.output)
        )

    if exit_stack is not None:
        return await _invoke_async_with_stack(exit_stack)

    async with contextlib.AsyncExitStack() as stack:
        return await _invoke_async_with_stack(stack)


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
) -> ParseResult[T, S]:
    concrete_backend = _coalesce_backend(backend)
    concrete_output = _coalesce_output(output, theme, color)
    concrete_state: State[S] = State.ensure(state)  # type: ignore

    command: FinalCommand[T] = collect(
        obj,
        help=help,
        version=version,
        completion=completion,
        backend=concrete_backend,
        help_formatter=help_formatter,
        state=concrete_state,
    )
    return command.parse_command(
        argv=argv,
        input=input,
        backend=concrete_backend,
        output=concrete_output,
        state=concrete_state,
    )


@overload
def command(
    _cls: type[T],
    *,
    name: str | None = None,
    aliases: list[str | Alias] | None = None,
    help: str | None = None,
    description: str | None = None,
    epilog: str | None = None,
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
    aliases: list[str | Alias] | None = None,
    help: str | None = None,
    description: str | None = None,
    epilog: str | None = None,
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
    aliases: list[str | Alias] | None = None,
    help: str | None = None,
    description: str | None = None,
    epilog: str | None = None,
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
    aliases: list[str | Alias] | None = None,
    help: str | None = None,
    description: str | None = None,
    epilog: str | None = None,
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
        aliases: Alternate names that may be used to invoke this command as a
            subcommand. Each entry is either a plain string (visible alias) or
            an :class:`Alias` instance (which can be marked `hidden=True` or
            `deprecated=...`). Only meaningful when the class is used as a
            subcommand.
        help: Optional help text. If omitted, the `cls` docstring will be parsed,
            and the headline section will be used to document the command
            itself, and the arguments section will become the default help text for
            any params/options.
        description: Optional extended help text. If omitted, the `cls` docstring will
            be parsed, and the extended long description section will be used.
        epilog: Optional text displayed after the argument list in the help output.
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
            aliases=list(aliases) if aliases is not None else command.aliases,
            help=help,
            description=description,
            epilog=epilog,
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
) -> FinalCommand[T]:
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

    command: FinalCommand[T] = Command.get(  # pyright: ignore
        obj, help_formatter=help_formatter
    ).collect(state=state)

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
