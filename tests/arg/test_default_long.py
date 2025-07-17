from __future__ import annotations

from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from cappa.output import Exit
from tests.utils import Backend, backends, parse


@backends
def test_valid(backend: Backend):
    @cappa.command(default_long=True)
    @dataclass
    class Command:
        foo: int = 4
        bar: int = 5

    test = parse(Command, backend=backend)
    assert test == Command(4, 5)

    test = parse(Command, "--foo", "1", "--bar", "2", backend=backend)
    assert test == Command(1, 2)


@backends
def test_override(backend: Backend):
    @cappa.command(default_long=True)
    @dataclass
    class Command:
        foo: int
        far: Annotated[int, cappa.Arg(long="--kar")]

    test = parse(Command, "--foo", "1", "--kar", "2", backend=backend)
    assert test == Command(1, 2)


@backends
def test_invalid(backend: Backend):
    @cappa.command(default_long=True)
    @dataclass
    class Command:
        foo: int
        far: Annotated[int, cappa.Arg(long="--foo")]

    with pytest.raises(Exit) as e:
        parse(Command, backend=backend)
    assert "conflicting option string: --f" in str(e.value.message).lower()
