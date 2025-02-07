from __future__ import annotations

import argparse
import sys
import typing
from collections.abc import Callable

from cappa.arg import Arg, ArgAction
from cappa.command import Command, Subcommand
from cappa.help import generate_arg_groups
from cappa.invoke import fulfill_deps
from cappa.output import Exit, HelpExit, Output
from cappa.parser import RawOption, Value
from cappa.typing import assert_never, assert_type

if sys.version_info < (3, 9):  # pragma: no cover
    # Backport https://github.com/python/cpython/pull/3680
    original_get_action_name = argparse._get_action_name

    def _get_action_name(
        argument: argparse.Action | None,
    ) -> str | None:  # pragma: no cover
        name = original_get_action_name(argument)

        assert argument
        if name is None and argument.choices:
            return "{" + ",".join(argument.choices) + "}"

        return name

    argparse._get_action_name = _get_action_name


T = typing.TypeVar("T")


# Work around argparse's lack of `metavar` support on various built-in actions.
class _HelpAction(argparse._HelpAction):
    def __init__(self, metavar=None, **kwargs):
        self.metavar = metavar
        super().__init__(**kwargs)


class _VersionAction(argparse._VersionAction):
    def __init__(self, metavar=None, **kwargs):
        self.metavar = metavar
        super().__init__(**kwargs)


class _StoreTrueAction(argparse._StoreTrueAction):
    def __init__(self, metavar=None, **kwargs):
        self.metavar = metavar
        super().__init__(**kwargs)


class _StoreFalseAction(argparse._StoreFalseAction):
    def __init__(self, metavar=None, **kwargs):
        self.metavar = metavar
        super().__init__(**kwargs)


class _CountAction(argparse._CountAction):
    def __init__(self, metavar=None, **kwargs):
        self.metavar = metavar
        super().__init__(**kwargs)


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, command: Command, output: Output, **kwargs):
        super().__init__(*args, **kwargs)
        self.command = command
        self.output = output

        self.register("action", "store_true", _StoreTrueAction)
        self.register("action", "store_false", _StoreFalseAction)
        self.register("action", "help", _HelpAction)
        self.register("action", "version", _VersionAction)
        self.register("action", "count", _CountAction)

    def error(self, message):
        # Avoids argparse's error prefixing code, deferring it to Output
        self.exit(2, message)

    def exit(self, status=0, message=None):
        if message:
            message = message.capitalize()

        raise Exit(message, code=status, prog=self.prog)

    def print_help(self, file=None):
        raise HelpExit(self.command.help_formatter(self.command, self.prog))


def custom_action(arg: Arg, action: Callable):
    class CustomAction(argparse.Action):
        def __call__(  # type: ignore
            self,
            parser: ArgumentParser,
            namespace,
            values,
            option_string=None,
        ):
            # XXX: This should ideally be able to inject parser state, but here, we dont
            #      have access to the same state as the native parser.
            fulfilled_deps: dict = {
                Output: parser.output,
                Value: Value(values),
                Command: namespace.__command__,
                Arg: arg,
            }
            if option_string:
                fulfilled_deps[RawOption] = RawOption.from_str(option_string)

            deps = fulfill_deps(action, fulfilled_deps)
            result = action(**deps.kwargs)
            setattr(namespace, self.dest, result)

    return CustomAction


class Nestedspace(argparse.Namespace):
    """Write each . separated section as a nested `Nestedspace` instance.

    By default, argparse write everything to a flat namespace so there's no
    obvious way to distinguish between multiple unrelated subcommands once
    once has been chosen.
    """

    def __setattr__(self, name, value):
        if "." in name:
            group, name = name.split(".", 1)
            ns = getattr(self, group, Nestedspace())
            setattr(ns, name, value)
            self.__dict__[group] = ns
        else:
            self.__dict__[name] = value


def backend(
    command: Command[T],
    argv: list[str],
    output: Output,
    prog: str,
) -> tuple[typing.Any, Command[T], dict[str, typing.Any]]:
    parser = create_parser(command, output=output, prog=prog)

    try:
        version = next(
            a
            for a in command.arguments
            if isinstance(a, Arg) and a.action is ArgAction.version
        )
        parser.version = version.value_name  # type: ignore
    except StopIteration:
        pass

    ns = Nestedspace()

    try:
        result_namespace = parser.parse_args(argv, ns)
    except argparse.ArgumentError as e:
        raise Exit(str(e), code=2, prog=prog)

    result = to_dict(result_namespace)
    command = result.pop("__command__")

    return parser, command, result


def create_parser(
    command: Command, output: Output, prog: str
) -> argparse.ArgumentParser:
    kwargs: dict[str, typing.Any] = {}
    if sys.version_info >= (3, 9):  # pragma: no cover
        kwargs["exit_on_error"] = False

    parser = ArgumentParser(
        command=command,
        output=output,
        prog=prog,
        description=join_help(command.help, command.description),
        allow_abbrev=False,
        add_help=False,
        **kwargs,
    )
    parser.set_defaults(__command__=command)

    add_arguments(parser, command, output=output)
    return parser


def add_arguments(
    parser: argparse.ArgumentParser, command: Command, output: Output, dest_prefix=""
):
    arg_groups = generate_arg_groups(command, include_hidden=True)
    for (group_name, group_exclusive), args in arg_groups:
        argparse_group = parser.add_argument_group(title=group_name)
        if group_exclusive:
            argparse_group = argparse_group.add_mutually_exclusive_group()

        for arg in args:
            if isinstance(arg, Arg):
                add_argument(argparse_group, arg, dest_prefix=dest_prefix)
            elif isinstance(arg, Subcommand):
                add_subcommands(
                    parser, group_name, arg, output=output, dest_prefix=dest_prefix
                )
            else:
                assert_never(arg)


def add_argument(
    parser: argparse.ArgumentParser | argparse._ArgumentGroup,
    arg: Arg,
    dest_prefix="",
    **extra_kwargs,
):
    if arg.propagate:
        raise ValueError("The argparse backend does not support the `Arg.propagate`.")

    names: list[str] = []
    if arg.short:
        short = assert_type(arg.short, list)
        names.extend(short)

    if arg.long:
        long = assert_type(arg.long, list)
        names.extend(long)

    is_positional = not names

    num_args = backend_num_args(arg.num_args, assert_type(arg.required, bool))

    kwargs: dict[str, typing.Any] = {
        "dest": dest_prefix + assert_type(arg.field_name, str),
        "help": arg.help,
        "metavar": arg.value_name,
        "action": get_action(arg),
        "default": argparse.SUPPRESS,
    }

    if not is_positional and arg.required and assert_type(arg.num_args, int) >= 0:
        kwargs["required"] = arg.required

    if num_args is not None and not ArgAction.is_non_value_consuming(arg.action):
        kwargs["nargs"] = num_args
    elif is_positional and not arg.required:
        kwargs["nargs"] = "?"

    deprecated_kwarg = add_deprecated_kwarg(arg)
    kwargs.update(deprecated_kwarg)
    kwargs.update(extra_kwargs)

    parser.add_argument(*names, **kwargs)


def add_subcommands(
    parser: argparse.ArgumentParser,
    group: str,
    subcommands: Subcommand,
    output: Output,
    dest_prefix="",
):
    subcommand_dest = subcommands.field_name
    subparsers = parser.add_subparsers(
        title=group,
        required=assert_type(subcommands.required, bool),
        parser_class=ArgumentParser,
    )

    for name, subcommand in subcommands.options.items():
        deprecated_kwarg = add_deprecated_kwarg(subcommand)

        nested_dest_prefix = f"{dest_prefix}{subcommand_dest}."
        subparser = subparsers.add_parser(
            name=subcommand.real_name(),
            help=subcommand.help,
            description=subcommand.description,
            formatter_class=parser.formatter_class,
            add_help=False,
            command=subcommand,  # type: ignore
            output=output,
            prog=f"{parser.prog} {subcommand.real_name()}",
            **deprecated_kwarg,
        )
        subparser.set_defaults(
            __command__=subcommand, **{nested_dest_prefix + "__name__": name}
        )

        add_arguments(
            subparser,
            subcommand,
            output=output,
            dest_prefix=nested_dest_prefix,
        )


def backend_num_args(num_args: int | None, required: bool) -> int | str | None:
    if num_args is None or num_args == 1:
        return None

    if num_args == -1:
        if required:
            return "+"
        return "*"

    return num_args


def to_dict(value: argparse.Namespace):
    result = {}
    for k, v in value.__dict__.items():
        if isinstance(v, argparse.Namespace):
            v = to_dict(v)
        result[k] = v

    return result


def join_help(*segments):
    return " ".join([s for s in segments if s])


def get_action(arg: Arg) -> argparse.Action | type[argparse.Action] | str:
    action = arg.action
    if isinstance(action, ArgAction):
        return action.value

    action = typing.cast(Callable, action)
    return custom_action(arg, action)


def add_deprecated_kwarg(arg: Arg | Command) -> dict[str, typing.Any]:
    if sys.version_info < (3, 13) or not arg.deprecated:
        return {}

    return {"deprecated": arg.deprecated}  # pragma: no cover
