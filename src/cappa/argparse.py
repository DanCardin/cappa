from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING, Any, Callable, Hashable, List, TypeVar, cast

from cappa.arg import Arg, ArgAction
from cappa.command import Command, Subcommand
from cappa.help import generate_arg_groups
from cappa.invoke import fulfill_deps
from cappa.output import Exit, HelpExit, Output
from cappa.parser import RawOption, Value
from cappa.typing import assert_type

if TYPE_CHECKING:
    from _typeshed import SupportsWrite

if sys.version_info < (3, 9):  # pragma: no cover
    # Backport https://github.com/python/cpython/pull/3680
    original_get_action_name = argparse._get_action_name  # pyright: ignore

    def _get_action_name(
        argument: argparse.Action | None,
    ) -> str | None:  # pragma: no cover
        name = original_get_action_name(argument)

        assert argument
        if name is None and argument.choices:
            return "{" + ",".join(argument.choices) + "}"

        return name

    argparse._get_action_name = _get_action_name  # pyright: ignore


T = TypeVar("T")


# Work around argparse's lack of `metavar` support on various built-in actions.
class _HelpAction(argparse._HelpAction):  # pyright: ignore
    def __init__(self, metavar: str | None = None, **kwargs: Any):
        self.metavar = metavar
        super().__init__(**kwargs)


class _VersionAction(argparse._VersionAction):  # pyright: ignore
    def __init__(self, metavar: str | None = None, **kwargs: Any):
        self.metavar = metavar
        super().__init__(**kwargs)


class _StoreTrueAction(argparse._StoreTrueAction):  # pyright: ignore
    def __init__(self, metavar: str | None = None, **kwargs: Any):
        self.metavar = metavar
        super().__init__(**kwargs)


class _StoreFalseAction(argparse._StoreFalseAction):  # pyright: ignore
    def __init__(self, metavar: str | None = None, **kwargs: Any):
        self.metavar = metavar
        super().__init__(**kwargs)


class _CountAction(argparse._CountAction):  # pyright: ignore
    def __init__(self, metavar: str | None = None, **kwargs: Any):
        self.metavar = metavar
        super().__init__(**kwargs)


class ArgumentParser(argparse.ArgumentParser):
    def __init__(
        self, *args: Any, command: Command[Any], output: Output, **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        self.command = command
        self.output = output

        self.register("action", "store_true", _StoreTrueAction)
        self.register("action", "store_false", _StoreFalseAction)
        self.register("action", "help", _HelpAction)
        self.register("action", "version", _VersionAction)
        self.register("action", "count", _CountAction)

    def error(self, message: str):
        # Avoids argparse's error prefixing code, deferring it to Output
        self.exit(2, message)

    def exit(self, status: int = 0, message: str | None = None):
        if message:
            message = message.capitalize()

        raise Exit(message, code=status, prog=self.prog)

    def print_help(self, file: SupportsWrite[str] | None = None):
        raise HelpExit(self.command.help_formatter(self.command, self.prog))


def custom_action(arg: Arg[Any], action: Callable[..., Any]):
    class CustomAction(argparse.Action):
        def __call__(  # type: ignore
            self,
            parser: ArgumentParser,
            namespace: argparse.Namespace,
            values: Any,
            option_string: str | None = None,
        ):
            # XXX: This should ideally be able to inject parser state, but here, we dont
            #      have access to the same state as the native parser.
            fulfilled_deps: dict[Hashable, Any] = {
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

    def __setattr__(self, name: str, value: Any):
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
    provide_completions: bool = False,
) -> tuple[Any, Command[T], dict[str, Any]]:
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
    command: Command[Any], output: Output, prog: str
) -> argparse.ArgumentParser:
    kwargs: dict[str, Any] = {}
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
    parser: ArgumentParser,
    command: Command[Any],
    output: Output,
    dest_prefix: str = "",
):
    arg_groups = generate_arg_groups(command, include_hidden=True)
    for (group_name, group_exclusive), args in arg_groups:
        argparse_group = parser.add_argument_group(title=group_name)
        if group_exclusive:
            argparse_group = argparse_group.add_mutually_exclusive_group()

        for arg in args:
            if isinstance(arg, Arg):
                add_argument(parser, argparse_group, arg, dest_prefix=dest_prefix)
            else:
                add_subcommands(
                    parser, group_name, arg, output=output, dest_prefix=dest_prefix
                )


def add_argument(
    parser: ArgumentParser,  # pyright: ignore
    subparser: argparse.ArgumentParser | argparse._ArgumentGroup,  # pyright: ignore
    arg: Arg[Any],
    dest_prefix: str = "",
    **extra_kwargs: Any,
):
    if arg.propagate:
        raise RuntimeError("The argparse backend does not support the `Arg.propagate`.")

    names: list[str] = []
    if arg.short:
        short = cast(List[str], arg.short)
        names.extend(short)

    if arg.long:
        long = cast(List[str], arg.long)
        names.extend(long)

    is_positional = not names

    num_args = backend_num_args(arg.num_args, assert_type(arg.required, bool))

    kwargs: dict[str, Any] = {
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

    try:
        subparser.add_argument(*names, **kwargs)
    except argparse.ArgumentError as e:
        raise Exit(str(e), code=2, prog=parser.prog)


def add_subcommands(
    parser: argparse.ArgumentParser,
    group: str,
    subcommands: Subcommand,
    output: Output,
    dest_prefix: str = "",
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
            command=subcommand,
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
    result: dict[str, Any] = {}
    for k, v in value.__dict__.items():
        if isinstance(v, argparse.Namespace):
            v = to_dict(v)
        result[k] = v

    return result


def join_help(*segments: str | None):
    return " ".join([s for s in segments if s])


def get_action(arg: Arg[Any]) -> argparse.Action | type[argparse.Action] | str:
    action = arg.action
    if isinstance(action, ArgAction):
        return action.value

    action = cast(Callable[..., Any], action)
    return custom_action(arg, action)


def add_deprecated_kwarg(arg: Arg[Any] | Command[Any]) -> dict[str, Any]:
    if sys.version_info < (3, 13) or not arg.deprecated:
        return {}

    return {"deprecated": arg.deprecated}  # pragma: no cover
