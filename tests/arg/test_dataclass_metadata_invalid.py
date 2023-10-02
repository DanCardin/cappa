from __future__ import annotations

from dataclasses import dataclass, field

import cappa
import pytest

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
    with pytest.raises(
        ValueError,
        match='`metadata={"cappa": <x>}` must be of type `Arg` or `Subcommand`',
    ):
        parse(Command, "-n", "foo", "subcommand", "4", backend=backend)
