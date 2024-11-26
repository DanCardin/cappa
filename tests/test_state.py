from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from typing_extensions import Annotated

import cappa
from cappa.default import ValueFrom
from cappa.state import State
from tests.utils import backends, invoke, parse


class Increment(TypedDict):
    value: int


def woah(state: State):
    state.state["value"] = state.state.get("value", 0) + 1
    return state.state["value"]


@dataclass
class Command:
    foo: Annotated[int, cappa.Arg(default=ValueFrom(woah))] = 0
    bar: Annotated[int, cappa.Arg(default=ValueFrom(woah))] = 0

    def __call__(self, state: State):
        return state.state


@backends
def test_shared_state(backend):
    result = parse(Command, "6", "7", backend=backend)
    assert result == Command(6, 7)

    result = parse(Command, backend=backend)
    assert result == Command(1, 2)


@backends
def test_dep_state(backend):
    result = invoke(Command, "6", "7", backend=backend)
    assert result == {}

    result = invoke(Command, backend=backend)
    assert result == {"value": 2}


def parse_val(value, state: State):
    state.set("foo", int(value))
    return state.get("foo")


@backends
def test_parse_state(backend):
    state: State = State()

    @dataclass
    class Command:
        foo: Annotated[int, cappa.Arg(parse=parse_val)] = 0

    result = parse(Command, backend=backend, state=state)
    assert result == Command(0)
    assert state.get("foo") is None

    result = parse(Command, "6", backend=backend, state=state)
    assert result == Command(6)
    assert state.get("foo") == 6
