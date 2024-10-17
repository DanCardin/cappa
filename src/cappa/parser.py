from __future__ import annotations

import dataclasses
import typing
from collections import deque

from cappa.arg import Arg, ArgAction, ArgActionType, Group
from cappa.command import Command, Subcommand
from cappa.completion.types import Completion, FileCompletion
from cappa.help import format_subcommand_names
from cappa.invoke import fulfill_deps
from cappa.output import Exit, HelpExit, Output
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


@dataclasses.dataclass
class HelpAction(RuntimeError):
    command: Command
    command_name: str

    @classmethod
    def from_context(cls, context: ParseContext, command: Command):
        name = " ".join(c.real_name() for c in context.command_stack)
        raise cls(command, name)


@dataclasses.dataclass
class VersionAction(RuntimeError):
    version: Arg

    @classmethod
    def from_arg(cls, arg: Arg):
        raise cls(arg)


class CompletionAction(RuntimeError):
    def __init__(
        self,
        *completions: Completion | FileCompletion,
        value="complete",
        arg: Arg | None = None,
    ) -> None:
        self.completions = completions
        self.value = value
        self.arg = arg

    @classmethod
    def from_value(cls, value: Value[str], arg: Arg):
        raise cls(value=value.value, arg=arg)


def backend(
    command: Command[T],
    argv: list[str],
    output: Output,
    prog: str,
    provide_completions: bool = False,
) -> tuple[typing.Any, Command[T], dict[str, typing.Any]]:
    args = RawArg.collect(argv, provide_completions=provide_completions)

    context = ParseContext.from_command(args, [command], output)
    context.provide_completions = provide_completions

    try:
        try:
            parse(context)
        except HelpAction as e:
            raise HelpExit(
                e.command.help_formatter(e.command, e.command_name),
                code=0,
                prog=context.prog,
            )
        except VersionAction as e:
            raise Exit(
                typing.cast(str, e.version.value_name), code=0, prog=context.prog
            )
        except BadArgumentError as e:
            if context.provide_completions and e.arg:
                completions = e.arg.completion(e.value) if e.arg.completion else []
                raise CompletionAction(*completions)

            raise Exit(str(e), code=2, prog=context.prog, command=e.command)
    except CompletionAction as e:
        from cappa.completion.base import execute, format_completions

        if context.provide_completions:
            completions = format_completions(*e.completions)
            raise Exit(completions, code=0)

        execute(command, prog, e.value, assert_type(e.arg, Arg), output=output)

    if provide_completions:
        raise Exit(code=0)

    return (context, context.command_stack[-1] or command, context.result)


@dataclasses.dataclass
class ParseContext:
    remaining_args: deque[RawArg | RawOption]
    options: dict[str, Arg]
    arguments: deque[Arg | Subcommand]
    missing_options: set[str]

    output: Output

    consumed_args: list[RawArg | RawOption] = dataclasses.field(default_factory=list)
    exclusive_args: dict[str, Arg] = dataclasses.field(default_factory=dict)

    result: dict[str, typing.Any] = dataclasses.field(default_factory=dict)
    command_stack: list[Command] = dataclasses.field(default_factory=list)

    provide_completions: bool = False

    @classmethod
    def from_command(
        cls,
        args: deque[RawArg | RawOption],
        command_stack: list[Command],
        output: Output,
    ) -> ParseContext:
        command = command_stack[-1]
        options, missing_options = cls.collect_options(command)
        arguments = deque(cls.collect_arguments(command))
        return cls(
            args,
            options,
            arguments,
            output=output,
            missing_options=missing_options,
            command_stack=command_stack,
        )

    @staticmethod
    def collect_options(command: Command) -> tuple[dict[str, Arg], set[str]]:
        result = {}
        unique_names = set()
        for arg in command.arguments:
            field_name = typing.cast(str, arg.field_name)
            if not isinstance(arg, Arg):
                continue

            if arg.short or arg.long:
                if arg.action not in ArgAction.value_actions():
                    unique_names.add(field_name)
                result[field_name] = arg

            for opts in (arg.short, arg.long):
                if not opts:
                    continue

                for key in typing.cast(typing.List[str], opts):
                    if key in result:
                        raise ValueError(f"Conflicting option string: {key}")

                    result[key] = arg

        return result, unique_names

    @staticmethod
    def collect_arguments(command: Command) -> list[Arg | Subcommand]:
        result = []
        for arg in command.arguments:
            if (
                isinstance(arg, Arg)
                and not arg.short
                and not arg.long
                and not arg.destructured
            ) or isinstance(arg, Subcommand):
                result.append(arg)
        return result

    @property
    def prog(self):
        return " ".join(c.real_name() for c in self.command_stack)

    @property
    def command(self):
        return self.command_stack[-1]

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


@dataclasses.dataclass
class RawArg:
    raw: str
    end: bool = False

    @classmethod
    def collect(
        cls, argv: list[str], *, provide_completions: bool = False
    ) -> deque[RawArg | RawOption]:
        result: list[RawArg | RawOption] = []

        encountered_double_dash = False
        for arg in argv:
            if encountered_double_dash:
                item: RawArg | RawOption | None = cls(arg)
            else:
                item = RawArg.from_str(arg, provide_completions=provide_completions)

            if item is None:
                encountered_double_dash = True

                # Indicate to the arg consumption loop that it should stop consuming the
                # current argument. Irrelevant to options, whose name-argument is consumed
                # ahead of the value.
                if result:
                    result[-1].end = True
            else:
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


@dataclasses.dataclass
class RawOption:
    name: str
    is_long: bool
    value: str | None = None
    end: bool = False

    @classmethod
    def from_str(cls, arg: str) -> RawOption:
        is_long = arg.startswith("--")
        is_explicit = "=" in arg

        name = arg
        value = None
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

    # Options are not explicitly iterated over because they can occur multiple times non-contiguouesly.
    # So instead we check afterward, if there are any missing which we haven't yet fulfilled.
    required_missing_options = [
        context.options[opt_name]
        for opt_name in sorted(context.missing_options)
        if context.options[opt_name].required
    ]
    if required_missing_options:
        names = ", ".join([opt.names_str("/") for opt in required_missing_options])
        raise BadArgumentError(
            f"The following arguments are required: {names}",
            value="",
            command=context.command,
            arg=required_missing_options[0],
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
            raise CompletionAction(*options)

        message = f"Unrecognized arguments: {raw.name}"
        if possible_values:
            message += f" (Did you mean: {', '.join(possible_values)})"

        raise BadArgumentError(message, value=raw.name, command=context.command)

    arg = context.options[raw.name]

    consume_arg(context, arg, raw)


def parse_short_option(context: ParseContext, arg: RawOption) -> None:
    if arg.name == "-" and context.provide_completions:
        return parse_option(context, arg)

    virtual_options, virtual_arg = generate_virtual_args(arg, context.options)
    *first_virtual_options, last_virtual_option = virtual_options

    for opt in first_virtual_options:
        parse_option(context, opt)

    if virtual_arg:
        context.remaining_args.appendleft(virtual_arg)

    parse_option(context, last_virtual_option)
    return None


def generate_virtual_args(
    arg: RawOption, options: dict[str, typing.Any]
) -> tuple[list[RawOption], RawArg | None]:
    """Produce "virtual" options from short (potentially concatenated) options.

    Examples:
        -abc -> -a, -b, -c
        -c0 -> -c 0
        -abc0 -> -a, -b, -c, 0
    """
    result = []

    partial_arg = ""
    remaining_arg = arg.name[1:]
    while remaining_arg:
        partial_arg += remaining_arg[0]
        remaining_arg = remaining_arg[1:]

        option_name = f"-{partial_arg}"

        option = options.get(option_name)
        if option:
            result.append(RawOption(option_name, is_long=True, value=arg.value))
            partial_arg = ""

            # An option which requires consuming further arguments should consume
            # the rest of the concatenated character sequence as its value.
            if option.num_args:
                partial_arg = remaining_arg
                break

    if not result:
        # i.e. -p, where -p is not a real short option. It will get skipped above.
        return ([RawOption(arg.name, is_long=True, value=arg.value)], None)

    raw_arg = None
    if partial_arg:
        raw_arg = RawArg(partial_arg)

    return (result, raw_arg)


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
            next_val = context.next_value()
            if not isinstance(next_val, RawArg):
                break
            raw_values.append(next_val.raw)

        raise BadArgumentError(
            f"Unrecognized arguments: {', '.join(raw_values)}",
            value=raw_values,
            command=context.command,
        )


def consume_subcommand(context: ParseContext, arg: Subcommand) -> typing.Any:
    try:
        value = context.next_value()
    except IndexError:
        if not arg.required:
            return

        raise BadArgumentError(
            f"A command is required: {{{format_subcommand_names(arg.names())}}}",
            value="",
            command=context.command,
            arg=arg,
        )

    assert isinstance(value, RawArg), value
    if value.raw not in arg.options:
        message = f"Invalid command '{value.raw}'"
        possible_values = [name for name in arg.names() if name.startswith(value.raw)]
        if possible_values:
            message += f" (Did you mean: {format_subcommand_names(possible_values)})"

        raise BadArgumentError(
            message,
            value=value.raw,
            command=context.command,
            arg=arg,
        )

    command = arg.options[value.raw]
    check_deprecated(context, command)

    context.command_stack.append(command)

    nested_context = ParseContext.from_command(
        context.remaining_args,
        command_stack=context.command_stack,
        output=context.output,
    )
    nested_context.provide_completions = context.provide_completions
    nested_context.result["__name__"] = value.raw

    parse(nested_context)

    name = typing.cast(str, arg.field_name)
    context.result[name] = nested_context.result


def consume_arg(
    context: ParseContext, arg: Arg, option: RawOption | None = None
) -> typing.Any:
    field_name = typing.cast(str, arg.field_name)

    orig_num_args = arg.num_args if arg.num_args is not None else 1
    num_args = orig_num_args

    if ArgAction.is_non_value_consuming(arg.action):
        orig_num_args = 0
        num_args = 0

    result: list[str] | str = []
    requires_values = True
    if option:
        if option.value:
            result = [option.value]
            requires_values = False

        if option.end:
            requires_values = False

    if requires_values:
        result = []
        while num_args:
            if isinstance(context.peek_value(), RawOption):
                break

            try:
                next_val = typing.cast(RawArg, context.next_value())
            except IndexError:
                break

            result.append(next_val.raw)

            if next_val.end:
                break

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
                if arg.completion:
                    completions: list[Completion] | list[FileCompletion] = (
                        arg.completion(result)
                    )
                else:
                    completions = [FileCompletion(result)]
                raise CompletionAction(*completions)
        else:
            if not option and not arg.required:
                return

            raise BadArgumentError(
                f"Option '{arg.value_name}' requires an argument",
                value="",
                command=context.command,
                arg=arg,
            )
    else:
        if orig_num_args > 0 and len(result) != orig_num_args:
            quoted_result = [f"'{r}'" for r in result]
            names_str = arg.names_str("/")

            message = f"Argument '{names_str}' requires {orig_num_args} values, found {len(result)}"
            if quoted_result:
                message += f" ({', '.join(quoted_result)} so far)"
            raise BadArgumentError(
                message,
                value=result,
                command=context.command,
                arg=arg,
            )

    group = typing.cast(typing.Optional[Group], arg.group)
    if group and group.exclusive:
        group_name = typing.cast(str, group.name)
        exclusive_arg = context.exclusive_args.get(group_name)

        if exclusive_arg and exclusive_arg != arg:
            raise BadArgumentError(
                f"Argument '{arg.names_str('/')}' is not allowed with argument"
                f" '{exclusive_arg.names_str('/')}'",
                value=result,
                command=context.command,
                arg=arg,
            )

        context.exclusive_args[group_name] = arg

    if option and field_name in context.missing_options:
        context.missing_options.remove(field_name)

    action_handler = determine_action_handler(arg.action)

    fulfilled_deps: dict = {
        Command: context.command,
        Output: context.output,
        ParseContext: context,
        Arg: arg,
        Value: Value(result),
    }
    if option:
        fulfilled_deps[RawOption] = option

    kwargs = fulfill_deps(action_handler, fulfilled_deps).kwargs
    result = action_handler(**kwargs)
    if arg.has_value:
        context.result[field_name] = result

    check_deprecated(context, arg, option)


def check_deprecated(
    context: ParseContext, arg: Arg | Command, option: RawOption | None = None
) -> None:
    if not arg.deprecated:
        return

    if option:
        kind = "Option"
        name = option.name
    else:
        if isinstance(arg, Command):
            kind = "Command"
            name = arg.real_name()
        else:
            kind = "Argument"
            name = arg.names_str("/")

    message = f"{kind} `{name}` is deprecated"
    if isinstance(arg.deprecated, str):
        message += f": {arg.deprecated}"

    context.output.error(message)


@dataclasses.dataclass
class Value(typing.Generic[T]):
    value: T


def store_true():
    return True


def store_false():
    return False


def store_count(context: ParseContext, arg: Arg):
    return context.result.get(typing.cast(str, arg.field_name), 0) + 1


def store_set(value: Value[typing.Any]):
    return value.value


def store_append(context: ParseContext, arg: Arg, value: Value[typing.Any]):
    result = context.result.setdefault(typing.cast(str, arg.field_name), [])
    result.append(value.value)
    return result


def determine_action_handler(action: ArgActionType | None):
    assert action

    if isinstance(action, ArgAction):
        return process_options[action]

    return action


process_options: dict[ArgAction, typing.Callable] = {
    ArgAction.help: HelpAction.from_context,
    ArgAction.version: VersionAction.from_arg,
    ArgAction.completion: CompletionAction.from_value,
    ArgAction.set: store_set,
    ArgAction.store_true: store_true,
    ArgAction.store_false: store_false,
    ArgAction.count: store_count,
    ArgAction.append: store_append,
}
