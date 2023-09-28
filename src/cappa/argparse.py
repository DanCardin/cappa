from __future__ import annotations

import argparse
import sys
import typing

from typing_extensions import assert_never

from cappa.arg import Arg, ArgAction
from cappa.command import Command, Subcommands
from cappa.output import Exit
from cappa.typing import assert_not_missing, assert_type, missing

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
    def __init__(self, *args, exit_with, **kwargs):
        self.exit_with = exit_with
        super().__init__(*args, **kwargs)

        self.register("action", "store_true", _StoreTrueAction)
        self.register("action", "store_false", _StoreFalseAction)
        self.register("action", "help", _HelpAction)
        self.register("action", "version", _VersionAction)
        self.register("action", "count", _CountAction)

    def exit(self, status=0, message=None):
        raise self.exit_with(message, code=status)


class BooleanOptionalAction(argparse.Action):
    """Simplified backport of same-named class from 3.9 onward.

    We know more about the called context here, and thus need much less of the
    logic. Also, we support 3.8, which does not have the original class, so we
    couldn't use it anyway.
    """

    def __init__(self, **kwargs):
        super().__init__(nargs=0, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        assert isinstance(option_string, str)
        setattr(namespace, self.dest, not option_string.startswith("--no-"))

    def format_usage(self):
        return " | ".join(self.option_strings)


class Nestedspace(argparse.Namespace):
    """Write each . separated section as a nested `Nestedspace` instance.

    By default, argparse write everything to a flat namespace so there's no
    obvious way to distinguish between mulitple unrelated subcommands once
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


def render(
    command: Command[T],
    argv: list[str],
    exit_with=None,
    color: bool = True,
    version: str | Arg | None = None,
    help: bool | Arg = True,
) -> tuple[Command[T], dict[str, typing.Any]]:
    if exit_with is None:
        exit_with = Exit

    parser = create_parser(command, exit_with, color=color)
    add_help_group(parser, version=version, help=help)

    ns = Nestedspace()

    try:
        result_namespace = parser.parse_args(argv[1:], ns)
    except argparse.ArgumentError as e:
        raise exit_with(str(e), code=127)
    except Exit as e:
        raise exit_with(e.message, code=e.code)

    result = to_dict(result_namespace)
    command = result.pop("__command__")

    return command, result


def create_parser(
    command: Command,
    exit_with: typing.Callable,
    color: bool = True,
) -> argparse.ArgumentParser:
    kwargs: dict[str, typing.Any] = {}
    if sys.version_info >= (3, 9):  # pragma: no cover
        kwargs["exit_on_error"] = False

    parser = ArgumentParser(
        prog=command.name,
        description=join_help(command.help, command.description),
        exit_with=exit_with,
        allow_abbrev=False,
        add_help=False,
        formatter_class=choose_help_formatter(color=color),
        **kwargs,
    )
    parser.set_defaults(__command__=command)

    add_arguments(parser, command)

    return parser


def add_help_group(
    parser: argparse.ArgumentParser,
    version: str | Arg | None = None,
    help: bool | Arg = True,
):
    if not version and not help:
        return

    help_group = parser.add_argument_group("help")
    if version:
        if isinstance(version, str):
            arg: Arg = Arg(
                version,
                short=["-v"],
                long=["--version"],
                help="Show the version and exit.",
            )
        else:
            arg = version.normalize()

        add_argument(help_group, arg, version=arg.name, action=_VersionAction)

    if help:
        if isinstance(help, bool):
            arg = Arg(
                name="help",
                short=["-h"],
                long=["--help"],
                help="Show this message and exit.",
            )
        else:
            arg = help.normalize()
            arg.name = "help"

        add_argument(help_group, arg, action=_HelpAction)


def choose_help_formatter(color: bool = True):
    help_formatter: type[
        argparse.HelpFormatter
    ] = argparse.ArgumentDefaultsHelpFormatter

    if color is True:
        try:
            from rich_argparse import ArgumentDefaultsRichHelpFormatter

            help_formatter = ArgumentDefaultsRichHelpFormatter
        except ImportError:  # pragma: no cover
            pass

    return help_formatter


def add_arguments(
    parser: argparse.ArgumentParser, command: Command, dest_prefix="", exit_with=Exit
):
    for arg in command.arguments:
        if isinstance(arg, Arg):
            add_argument(parser, arg, dest_prefix=dest_prefix)
        elif isinstance(arg, Subcommands):
            add_subcommands(parser, arg, dest_prefix=dest_prefix, exit_with=exit_with)
        else:
            assert_never(arg)


def add_argument(
    parser: argparse.ArgumentParser | argparse._ArgumentGroup,
    arg: Arg,
    dest_prefix="",
    **extra_kwargs,
):
    name: str = assert_not_missing(arg.name)

    names: list[str] = []
    if arg.short:
        short = assert_type(arg.short, list)
        names.extend(short)

    if arg.long:
        long = assert_type(arg.long, list)
        names.extend(long)

    is_positional = not names

    num_args = render_num_args(arg.num_args)

    kwargs: dict[str, typing.Any] = {
        "dest": dest_prefix + name,
        "help": arg.help,
        "metavar": name,
    }

    action = get_action(arg)
    if action:
        kwargs["action"] = action

    if not is_positional and arg.required:
        kwargs["required"] = arg.required

    if arg.default is not missing:
        if arg.action and arg.action is arg.action.append:
            kwargs["default"] = list(arg.default)  # type: ignore
        else:
            kwargs["default"] = arg.default

    if num_args is not None and (
        arg.action is None or arg.action is not arg.action.store_true
    ):
        kwargs["nargs"] = num_args
    elif is_positional and not arg.required:
        kwargs["nargs"] = "?"

    if arg.choices:
        kwargs["choices"] = arg.choices

    kwargs.update(extra_kwargs)

    parser.add_argument(*names, **kwargs)


def add_subcommands(
    parser: argparse.ArgumentParser,
    subcommands: Subcommands,
    dest_prefix="",
    exit_with=Exit,
):
    subcommand_dest = subcommands.name
    subparsers = parser.add_subparsers(
        title=subcommand_dest,
        required=subcommands.required,
        description=subcommands.help,
        parser_class=ArgumentParser,
    )

    for name, subcommand in subcommands.options.items():
        nested_dest_prefix = f"{dest_prefix}{subcommand_dest}."
        subparser = subparsers.add_parser(
            name=subcommand.real_name(),
            help=subcommand.help,
            description=subcommand.description,
            formatter_class=parser.formatter_class,
            exit_with=exit_with,  # type: ignore
        )
        subparser.set_defaults(
            __command__=subcommand, **{nested_dest_prefix + "__name__": name}
        )

        add_arguments(
            subparser,
            subcommand,
            dest_prefix=nested_dest_prefix,
        )


def render_num_args(num_args: int | None) -> int | str | None:
    if num_args is None:
        return None

    if num_args == -1:
        return "+"

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


def get_action(arg: Arg) -> type[argparse.Action] | str | None:
    if not arg.action:
        return None

    if arg.action in {ArgAction.store_true, ArgAction.store_false}:
        long = assert_type(arg.long, list)
        has_no_option = any("--no-" in i for i in long)
        if has_no_option:
            return BooleanOptionalAction

    return arg.action.value
