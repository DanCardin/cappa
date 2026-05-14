from __future__ import annotations

from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Hashable,
    Protocol,
    Type,
    TypeVar,
    Union,
    overload,
)

from cappa.state import S, State

if TYPE_CHECKING:
    from cappa.command import Command, FinalCommand
    from cappa.invoke.types import InvokeCallable, Resolved
    from cappa.output import Output


T = TypeVar("T")
U = TypeVar("U")

CappaCapable = Union["InvokeCallable[T]", Type[T], "Command[T]"]


class Backend(Protocol):
    def __call__(
        self,
        command: FinalCommand[T],
        argv: list[str],
        output: Output,
        prog: str,
        provide_completions: bool = False,
    ) -> tuple[Any, Command[T], dict[str, Any]]: ...  # pragma: no cover


class FuncOrClassDecorator(Protocol):
    @overload
    def __call__(self, x: type[T], /) -> type[T]: ...
    @overload
    def __call__(self, x: T, /) -> T: ...


@dataclass()
class ParseResult(Generic[T, S]):
    """Result of parsing a command with all collected metadata.

    Attributes:
        root_command: The root command that was parsed.
        parsed_command: The selected command (may be a subcommand if one was invoked).
        instance: The deferred instantiated command object.
        implicit_deps: Mapping of command classes to their deferred instances, collected during parsing.
        output: The output handler for the command.
        state: The state object for the command.
    """

    root_command: Command[T]
    parsed_command: Command[T]
    instance: Resolved[T]
    implicit_deps: dict[Hashable, Any]
    state: State[S]
    output: Output
