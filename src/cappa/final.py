from __future__ import annotations

from dataclasses import dataclass, replace
from functools import cached_property
from typing import TYPE_CHECKING, Callable, Generic, Iterable, TextIO, TypeVar

from cappa.arg import Arg
from cappa.arg_fields import ArgAction, ArgActionType, Group
from cappa.completion.types import Completion
from cappa.state import State
from cappa.type_view import Empty

if TYPE_CHECKING:
    from cappa.command import Command
    from cappa.completion.types import Completion
    from cappa.default import Default
    from cappa.destructure import Destructured
    from cappa.type_view import TypeView


T = TypeVar("T")


@dataclass(frozen=True)
class FinalArg(Arg, Generic[T]):
    value_name: str  # type: ignore
    field_name: str  # type: ignore
    type_view: TypeView  # type: ignore

    parse: Callable[..., T]  # type: ignore
    group: Group  # type: ignore
    action: ArgActionType  # type: ignore

    num_args: int  # type: ignore
    required: bool  # type: ignore
    has_value: bool  # type: ignore
    count: bool  # type: ignore
    hidden: bool  # type: ignore
    propagate: bool  # type: ignore
    show_default: bool  # type: ignore

    short: list[str] | None  # type: ignore
    long: list[str] | None  # type: ignore
    choices: list[str] | None  # type: ignore

    default: Default  # type: ignore
    help: str | None  # type: ignore

    deprecated: bool | str  # type: ignore

    completion: Callable[[str], list[Completion]] | None  # type: ignore
    destructured: Destructured | None  # type: ignore

    def names(self, *, n=0) -> list[str]:
        short_names = self.short or []
        long_names = self.long or []
        result = short_names + long_names
        if n:
            return result[:n]
        return result

    def names_str(self, delimiter: str = ", ", *, n=0) -> str:
        if self.long or self.short:
            return delimiter.join(self.names(n=n))

        return self.value_name

    @cached_property
    def is_option(self) -> bool:
        return bool(self.short or self.long)

    @classmethod
    def create_version_arg(cls, version: str | Arg | None = None) -> FinalArg | None:
        if not version:
            return None

        if isinstance(version, str):
            version = cls(
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

    @classmethod
    def create_help_arg(cls, help: bool | Arg | None = True) -> FinalArg | None:
        if not help:
            return None

        if isinstance(help, bool):
            help = cls(
                short=["-h"],
                long=["--help"],
                help="Show this message and exit.",
                group=Group(0, "Help", section=2),
                action=ArgAction.help,
            )

        return help.normalize(action=ArgAction.help, field_name="help", default=None)

    @classmethod
    def create_completion_arg(cls, completion: bool | Arg = True) -> FinalArg | None:
        if not completion:
            return None

        if isinstance(completion, bool):
            completion = cls(
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


@dataclass
class FinalSubcommand:
    """Describe a CLI subcommand.

    Arguments:
        field_name: Defaults to the name of the class, converted to dash case, but
            can be overridden here.
        required: Defaults to automatically inferring requiredness, based on whether the
            class's value has a default. By setting this, you can force a particular value.
        group: The subcommand group, for use in controlling help text for the subcommand, and
            where it is displayed. This can be any of: the string name (``'Subcommands'``),
            a 2-tuple of the `order` and the name (``(3, "Subcommands")``), or a :class:`Group`
            instance (``Group(3, 'Subcommands')``)
        hidden: Whether the argument should be hidden in help text. Defaults to False.
        options: A mapping of the subcommand names to the corresponding `Command` to which
            the subcommands refer. Unless imperatively constructing the CLI structure, this
            field should generally always be inferred automatically.
        types: Defaults to the class's annotated types, but can be overridden here.
    """

    field_name: str
    required: bool
    group: Group
    hidden: bool

    options: dict[str, Command]
    types: Iterable[type]

    def map_result(
        self,
        prog: str,
        parsed_args,
        state: State | None = None,
        input: TextIO | None = None,
    ):
        option_name = parsed_args.pop("__name__")
        option = self.options[option_name]
        return option.map_result(option, prog, parsed_args, state=state, input=input)

    def available_options(self) -> list[Command]:
        return [o for o in self.options.values() if not o.hidden]

    def names(self) -> list[str]:
        return [n for n, o in self.options.items() if not o.hidden]

    def names_str(self, delimiter: str = ", ") -> str:
        return f"{delimiter.join(self.names())}"

    def completion(self, partial: str):
        return [Completion(o) for o in self.options if partial in o]
