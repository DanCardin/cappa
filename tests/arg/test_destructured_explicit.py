from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import parse


@dataclass
class Config:
    color: Annotated[str, cappa.Arg(long=True)]


@dataclass
class Args:
    config: Annotated[Config, cappa.Arg.destructured()]


def test_destructured():
    test = parse(Args, "--color=red")
    assert test == Args(config=Config(color="red"))


@dataclass
class Args2:
    config: Annotated[Config, cappa.Arg(destructure=True)]


test = parse(Args2, "--color=red")
assert test == Args2(config=Config(color="red"))
