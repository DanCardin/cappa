from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict, Union

from typing_extensions import Annotated

import cappa
from cappa.output import Output
from cappa.state import State
from tests.utils import Backend, CapsysOutput, backends, invoke, parse


@backends
def test_no_op(backend: Backend):
    """Base case, this doesnt really serve any purpose."""

    def function():
        return 4

    parse(function, backend=backend)


@backends
def test_parse_one_arg(backend: Backend):
    """Parse with arguments.

    Again, not really a logical usecase for `parse`, but technically it ought to work.
    """

    def function(foo: str):
        return foo

    result = parse(function, "meow", backend=backend)
    assert result.foo == "meow"  # pyright: ignore


@backends
def test_invoke_base_case(backend: Backend):
    def function(foo: str):
        return foo

    result = invoke(function, "meow", backend=backend)
    assert result == "meow"


@backends
def test_invoke_optional_args(backend: Backend):
    def function(foo: Annotated[int, cappa.Arg(long=True)] = 15):
        return foo

    result = invoke(function, backend=backend)
    assert result == 15

    result = invoke(function, "--foo", "53", backend=backend)
    assert result == 53


@dataclass
class Sub:
    bar: Annotated[int, cappa.Arg(long=True)]

    def __call__(self):
        return self.bar + 1


@backends
def test_subcommand(backend: Backend):
    def function(sub: cappa.Subcommands[Union[Sub, None]] = None):
        assert sub is None
        return 6

    result = invoke(function, backend=backend)
    assert result == 6

    result = invoke(function, "sub", "--bar", "34", backend=backend)
    assert result == 35


def foo():
    return 5


@backends
def test_invoke_partial_arg_partial_dep(backend: Backend):
    def function(
        dep: Annotated[int, cappa.Dep(foo)],
        foo: Annotated[int, cappa.Arg(long=True)] = 15,
    ):
        return dep + foo

    result = invoke(function, backend=backend)
    assert result == 20

    result = invoke(function, "--foo", "53", backend=backend)
    assert result == 58


@backends
def test_output(backend: Backend, capsys: Any):
    """Depends on Output DI."""

    def function(foo: str, output: Output):
        output("hey")
        return foo

    result = invoke(function, "meow", backend=backend)
    assert result == "meow"

    out = CapsysOutput.from_capsys(capsys)
    assert out.stdout == "hey\n"


class StateFoo(TypedDict):
    foo: int


@backends
def test_state(backend: Backend, capsys: Any):
    """Depends on Output DI."""

    def function(foo: int, state: State[StateFoo]):
        return foo + state.state["foo"]

    state = State(StateFoo(foo=45))
    result = invoke(function, "3", backend=backend, state=state)
    assert result == 48
