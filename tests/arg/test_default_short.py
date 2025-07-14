from __future__ import annotations

from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from cappa.output import Exit
from tests.utils import Backend, backends, parse


@backends
def test_valid(backend: Backend):
    @cappa.command(default_short=True)
    @dataclass
    class Command:
        foo: int = 4
        bar: int = 5

    test = parse(Command, backend=backend)
    assert test == Command(4, 5)

    test = parse(Command, "-f", "1", "-b", "2", backend=backend)
    assert test == Command(1, 2)


@backends
def test_override(backend: Backend):
    @cappa.command(default_short=True)
    @dataclass
    class Command:
        foo: int
        far: Annotated[int, cappa.Arg(short="-k")]

    test = parse(Command, "-f", "1", "-k", "2", backend=backend)
    assert test == Command(1, 2)


@backends
def test_invalid(backend: Backend):
    @cappa.command(default_short=True)
    @dataclass
    class Command:
        foo: int
        far: int

    with pytest.raises(Exit) as e:
        parse(Command, backend=backend)
    assert "conflicting option string: -f" in str(e.value.message).lower()
