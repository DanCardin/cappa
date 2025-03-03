from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypedDict, TypeVar


class BaseTypedDict(TypedDict): ...


T = TypeVar("T", bound=BaseTypedDict)


@dataclass
class State(Generic[T]):
    """A store of arbitrary data.

    State can be used as arguments to `Arg.parse`, `Arg.action`,
    or `Arg.default=ValueFrom(...)` callables, as a way to propagate shared
    state between different parts of the overall parse execution.

    Example:
        >>> from typing_extensions import Annotated
        >>> import cappa

        >>> def parse_arg(state: State):
        ...     state.state["arg"] = state.state.get("arg", 0)
        ...     return state.state["arg"]

        >>> @dataclass
        ... class Command:
        ...     arg1: Annotated[int, cappa.Arg(action=parse_arg)]
        ...     arg2: Annotated[int, cappa.Arg(parse=parse_arg)]
        ...     arg3: Annotated[int, cappa.Arg(default=cappa.ValueFrom(parse_arg))]
    """

    state: T = field(default_factory=dict)  # type: ignore

    def set(self, key: str, value):
        self.state[key] = value  # type: ignore

    def get(self, key, *, default=None):
        return self.state.get(key, default)

    @classmethod
    def ensure(cls, state: State[T] | None) -> State[T]:
        if state is None:
            return State()
        return state
