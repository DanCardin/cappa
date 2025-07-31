from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Generic, TypedDict, TypeVar, Union, overload


class BaseTypedDict(TypedDict): ...


S = TypeVar("S", bound=Union[Dict[str, Any], BaseTypedDict])


@dataclass
class State(Generic[S]):
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

    state: S = field(default_factory=lambda: {})  # type: ignore

    def set(self, key: str, value: Any):
        self.state[key] = value  # type: ignore

    def get(self, key: str, *, default: Any = None):
        return self.state.get(key, default)

    @overload
    @classmethod
    def ensure(cls, state: None) -> State[dict[str, Any]]: ...

    @overload
    @classmethod
    def ensure(cls, state: State[S]) -> State[S]: ...

    @classmethod
    def ensure(cls, state: State[S] | None) -> State[S] | State[dict[str, Any]]:
        if state is None:
            return State()
        return state
