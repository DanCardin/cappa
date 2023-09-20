from __future__ import annotations

from dataclasses import dataclass

import cappa
from typing_extensions import Annotated

from tests.utils import parse


@dataclass
class Command:
    foo: Annotated[int, cappa.Arg(default=4)]
    bar: Annotated[int, cappa.Arg(default=5)]


def test_valid():
    test = parse(Command, "1", "2")
    assert test == Command(1, 2)
