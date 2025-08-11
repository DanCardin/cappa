from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import parse


@dataclass
class Config:
    verbose: Annotated[int, cappa.Arg(short=True, count=True)]


@dataclass
class Count:
    config: cappa.Destructured[Config]


def test_count():
    test = parse(Count, "-v")
    assert test == Count(config=Config(verbose=1))

    test = parse(Count, "-vvvvv")
    assert test == Count(config=Config(verbose=5))
