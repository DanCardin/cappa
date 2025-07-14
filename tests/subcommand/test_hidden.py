from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

import cappa
from tests.utils import Backend, backends, parse


@dataclass
class One: ...


@cappa.command(hidden=True)
@dataclass
class Two: ...


@dataclass
class Three: ...


@dataclass
class Command:
    sub: cappa.Subcommands[One | Two | Three]


@backends
def test_has_possible_values(capsys: Any, backend: Backend):
    with pytest.raises(cappa.Exit):
        parse(Command, "--help", backend=backend)

    out = capsys.readouterr().out
    assert "one" in out.lower()
    assert "two" not in out.lower()
    assert "three" in out.lower()

    cmd = parse(Command, "two", backend=backend)
    assert isinstance(cmd.sub, Two)
