from __future__ import annotations

from dataclasses import dataclass, field

import pytest

import cappa
from tests.utils import backends, parse


@dataclass
class Command:
    name: str = field(metadata={"cappa": cappa.Arg(short=True)})
    cmd: Invalid = field(metadata={"cappa": cappa.Subcommand()})


@dataclass
class Invalid:
    a: int = field(metadata={"cappa": 4})


@backends
def test_valid(backend):
    with pytest.raises(cappa.Exit) as e:
        parse(Command, "-n", "foo", "subcommand", "4", backend=backend)

    assert "invalid" in str(e.value.message).lower()
    assert "'subcommand'" in str(e.value.message)
