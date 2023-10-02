from __future__ import annotations

from dataclasses import dataclass

import cappa
from typing_extensions import Annotated

from tests.utils import backends, parse


@dataclass
class Command:
    foo: Annotated[int, cappa.Arg(default=4)]
    bar: Annotated[int, cappa.Arg(default=5)]


@backends
def test_valid(backend):
    test = parse(Command, "1", "2", backend=backend)
    assert test == Command(1, 2)
