from __future__ import annotations

from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Protocol,
    Type,
    TypeVar,
    Union,
    overload,
)

from cappa.state import S, State

if TYPE_CHECKING:
    from cappa.command import Command
    from cappa.invoke.types import InvokeCallable, Resolved
    from cappa.output import Output


T = TypeVar("T")
U = TypeVar("U")

CappaCapable = Union["InvokeCallable[T]", Type[T], "Command[T]"]


class Backend(Protocol):
    def __call__(
        self,
        command: Command[T],
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
    root_command: Command[T]
    parsed_command: Command[T]
    instance: Resolved[T]
    state: State[S]
    output: Output
