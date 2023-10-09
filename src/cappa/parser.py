from __future__ import annotations

import dataclasses
import os
import typing
from collections import deque

from cappa.arg import Arg, ArgAction, no_extra_arg_actions
from cappa.command import Command, Subcommand
from cappa.completion.types import Completion, CompletionError, FileCompletion
from cappa.help import (
    create_completion_arg,
    create_help_arg,
    create_version_arg,
    format_help,
)
from cappa.output import Exit, HelpExit
from cappa.typing import T, assert_type


class BadArgumentError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        value,
        command: Command,
        arg: Arg | Subcommand | None = None,
    ) -> None:
        super().__init__(message)
        self.value = value
        self.command = command
        self.arg = arg


class HelpAction(RuntimeError):
    def __init__(self, *, command, **_):
        self.command = command


class VersionAction(RuntimeError):
    def __init__(self, *, arg, **_):
        self.version = arg


def backend(
    command: Command[T],
    argv: list[str],
    color: bool = True,
    version: str | Arg | None = None,
    help: bool | Arg | None = True,
    completion: bool | Arg = True,
    provide_completions: bool = False,
) -> tuple[typing.Any, Command[T], dict[str, typing.Any]]:
    if not color:
        os.environ["NO_COLOR"] = "1"

    try:
        prog, *argv = argv
    except ValueError:
        prog = ""

    args = RawArg.collect(argv, provide_completions=provide_completions)

    help_arg = create_help_arg(help)
    version_arg = create_version_arg(version)
    completion_arg = create_completion_arg(completion)

    command.add_meta_actions(
        help=help_arg, version=version_arg, completion=completion_arg
    )

    context = ParseContext.from_command(command, args)
    context.provide_completions = provide_completions

    try:
        try:
            parse(context)
        except HelpAction as e:
            raise HelpExit(format_help(e.command, prog), code=0)
        except VersionAction as e:
            raise Exit(e.version.name, code=0)
        except BadArgumentError as e:
            if context.provide_completions and e.arg:
                completions = e.arg.completion(e.value) if e.arg.completion else []
                raise CompletionError(*completions)

            format_help(e.command, prog)
            raise Exit(str(e), code=2)
    except CompletionError as e:
        from cappa.completion.base import execute, format_completions

        if context.provide_completions:
            completions = format_completions(*e.completions)
            raise Exit(completions, code=0)

        execute(
            command,
            prog,
            e.value,
            help=help_arg,
            version=version_arg,
            completion=assert_type(completion_arg, Arg),
        )

    if provide_completions:
        raise Exit(code=0)

    return (context, context.selected_command or command, context.result)


@dataclasses.dataclass
class ParseContext:
    command: Command
    remaining_args: deque[RawArg | RawOption]
    options: dict[str, Arg]
    arguments: deque[Arg | Subcommand]
    missing_options: set[str]

    consumed_args: list[RawArg | RawOption] = dataclasses.field(default_factory=list)

    result: dict[str, typing.Any] = dataclasses.field(default_factory=dict)
    selected_command: Command | None = None

    provide_completions: bool = False

    @classmethod
    def from_command(
        cls,
        command: Command,
        args: deque[RawArg | RawOption],
    ) -> ParseContext:
        options, missing_options = cls.collect_options(command)
        arguments = deque(cls.collect_arguments(command))
        return cls(command, args, options, arguments, missing_options=missing_options)

    @staticmethod
    def collect_options(command: Command) -> tuple[dict[str, Arg], set[str]]:
        result = {}
        unique_names = set()
        for arg in command.arguments:
            if not isinstance(arg, Arg):
                continue

            if arg.short or arg.long:
                if arg.action not in ArgAction.value_actions():
                    unique_names.add(arg.name)
                result[arg.name] = arg

            assert arg.short is not True
            for short in arg.short or []:
                result[short] = arg

            assert arg.long is not True
            for long in arg.long or []:
                result[long] = arg

        return result, unique_names

    @staticmethod
    def collect_arguments(command: Command) -> list[Arg | Subcommand]:
        result = []
        for arg in command.arguments:
            if (
                isinstance(arg, Arg)
                and not arg.short
                and not arg.long
                or isinstance(arg, Subcommand)
            ):
                result.append(arg)
        return result

    def has_values(self) -> bool:
        return bool(self.remaining_args)

    def peek_value(self):
        if not self.remaining_args:
            return None
        return self.remaining_args[0]

    def next_value(self):
        arg = self.remaining_args.popleft()
        self.consumed_args.append(arg)
        return arg

    def next_argument(self):
        return self.arguments.popleft()


@dataclasses.dataclass(frozen=True)
class RawArg:
    raw: str

    @classmethod
    def collect(
        cls, argv: list[str], *, provide_completions: bool = False
    ) -> deque[RawArg | RawOption]:
        result = []

        encountered_double_dash = False
        for arg in argv:
            if encountered_double_dash:
                item: RawArg | RawOption | None = cls(arg)
            else:
                item = RawArg.from_str(arg, provide_completions=provide_completions)

            if item is None:
                encountered_double_dash = True
                continue

            result.append(item)

        return deque(result)

    @classmethod
    def from_str(
        cls, arg: str, *, provide_completions: bool = False
    ) -> RawArg | RawOption | None:
        skip = arg == "--" and not provide_completions
        if skip:
            return None

        is_option = arg and arg[0] == "-" and (provide_completions or len(arg) > 1)

        if is_option:
            return RawOption.from_str(arg)

        return cls(arg)


@dataclasses.dataclass(frozen=True)
class RawOption:
    name: str
    is_long: bool
    value: str | None = None

    @classmethod
    def from_str(cls, arg: str) -> RawOption:
        is_long = arg.startswith("--")

        name = arg
        value = None
        if is_long:
            is_explicit = "=" in arg
            if is_explicit:
                name, value = arg.split("=")
        return cls(name=name, is_long=is_long, value=value)


def parse(context: ParseContext) -> None:
    while True:
        while isinstance(context.peek_value(), RawOption):
            arg = typing.cast(RawOption, context.next_value())

            if arg.is_long:
                parse_option(context, arg)
            else:
                parse_short_option(context, arg)

        parse_args(context)

        if not context.has_values():
            break

    # Options are not explicitly iterated over because they can occur multi times non-contiguouesly.
    # So instead we check afterward, if there are any missing which we haven't yet fulfilled.
    for opt_name in context.missing_options:
        opt = context.options[opt_name]
        if opt.required:
            raise BadArgumentError(
                f"The following arguments are required: {opt.names_str()}",
                value="",
                command=context.command,
                arg=opt,
            )


def parse_option(context: ParseContext, raw: RawOption) -> None:
    if raw.name not in context.options:
        possible_values = [
            name for name in context.options if name.startswith(raw.name)
        ]

        if context.provide_completions:
            options = [
                Completion(option, help=context.options[option].help)
                for option in possible_values
            ]
            raise CompletionError(*options)

        message = f"Unrecognized arguments: {raw.name}"
        if possible_values:
            message += f" (Did you mean: {', '.join(possible_values)})"

        raise BadArgumentError(message, value=raw.name, command=context.command)

    arg = context.options[raw.name]
    consume_arg(context, arg, raw)


def parse_short_option(context: ParseContext, arg: RawOption) -> None:
    if arg.name == "-" and context.provide_completions:
        return parse_option(context, arg)

    for ch in arg.name[1:]:
        opt = RawOption(f"-{ch}", is_long=True)
        parse_option(context, opt)
    return None


def parse_args(context: ParseContext) -> None:
    while context.arguments:
        if isinstance(context.peek_value(), RawOption):
            break

        arg = context.next_argument()

        if isinstance(arg, Subcommand):
            consume_subcommand(context, arg)
        else:
            consume_arg(context, arg)
    else:
        value = context.peek_value()
        if value is None or isinstance(value, RawOption):
            return

        raw_values = []
        while context.peek_value():
            raw = typing.cast(RawArg, context.next_value()).raw
            raw_values.append(raw)

        raise BadArgumentError(
            f"Unrecognized arguments: {', '.join(raw_values)}",
            value=raw_values,
            command=context.command,
        )


def consume_arg(
    context: ParseContext, arg: Arg, option: RawOption | None = None
) -> typing.Any:
    orig_num_args = arg.num_args or 1
    num_args = orig_num_args

    if arg.action in no_extra_arg_actions:
        orig_num_args = 0
        num_args = 0

    result: list[str] | str
    if option and option.value:
        result = [option.value]
    else:
        result = []
        while num_args:
            try:
                value = context.next_value()
            except IndexError:
                break

            if isinstance(value, RawOption):
                raise BadArgumentError(
                    f"Argument requires {orig_num_args} values, "
                    f"only found {len(result)} ('{' '.join(result)}' so far).",
                    value=result,
                    command=context.command,
                    arg=arg,
                )

            result.append(value.raw)

            # If num-args starts at -1, then it will always be truthy when we subtract
            # from it. I.e. it has unbounded length, like we want.
            num_args -= 1

    if orig_num_args == 1:
        if result:
            result = result[0]
            if arg.choices and result not in arg.choices:
                choices = ", ".join(f"'{c}'" for c in arg.choices)
                raise BadArgumentError(
                    f"Invalid choice: '{result}' (choose from {choices})",
                    value=result,
                    command=context.command,
                    arg=arg,
                )

            if context.provide_completions and not context.has_values():
                raise CompletionError(FileCompletion(result))
        else:
            if not option and not arg.required:
                return

            raise BadArgumentError(
                f"Option '{arg.name}' requires an argument.",
                value="",
                command=context.command,
                arg=arg,
            )

    if option and arg.name in context.missing_options:
        context.missing_options.remove(arg.name)

    action = typing.cast(ArgAction, arg.action)
    name = typing.cast(str, arg.name)
    action_handler = process_options[action]
    existing_result = context.result.get(name)
    context.result[name] = action_handler(
        command=context.command,
        arg=arg,
        option_name=option and option.name,
        existing=existing_result,
        value=result,
    )


def consume_subcommand(context: ParseContext, arg: Subcommand) -> typing.Any:
    try:
        value = context.next_value()
    except IndexError:
        if not arg.required:
            return

        raise BadArgumentError(
            f"The following arguments are required: {arg.names_str()}",
            value="",
            command=context.command,
            arg=arg,
        )

    assert isinstance(value, RawArg), value
    if value.raw not in arg.options:
        raise BadArgumentError(
            "invalid subcommand", value=value.raw, command=context.command, arg=arg
        )

    command = arg.options[value.raw]
    context.selected_command = command

    nested_context = ParseContext.from_command(command, context.remaining_args)
    nested_context.provide_completions = context.provide_completions
    nested_context.result["__name__"] = value.raw

    parse(nested_context)

    name = typing.cast(str, arg.name)
    context.result[name] = nested_context.result
    if nested_context.selected_command:
        context.selected_command = nested_context.selected_command


def raises(exc):
    def store(**value):
        raise exc(**value)

    return store


def store_bool(val: bool):
    def store(arg, option_name: str, **_):
        long = assert_type(arg.long, list)
        has_no_option = any("--no-" in i for i in long)
        if has_no_option:
            return not option_name.startswith("--no-")
        return val

    return store


def store_count(*, existing: int | None, **_):
    return (existing or 0) + 1


def store_set(*, value, **_):
    return value


def store_append(*, existing, value, **_):
    return (existing or []) + [value]


process_options = {
    ArgAction.help: raises(HelpAction),
    ArgAction.version: raises(VersionAction),
    ArgAction.completion: raises(CompletionError),
    ArgAction.set: store_set,
    None: store_set,
    ArgAction.store_true: store_bool(True),
    ArgAction.store_false: store_bool(False),
    ArgAction.count: store_count,
    ArgAction.append: store_append,
}
