from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from typing_extensions import Annotated

import cappa
from tests.utils import parse


@dataclass
class Args:
    flavors: list[Literal["chocolate", "vanilla"]]
    something: Annotated[int, cappa.Arg(short="-p")] = 9


def test_destructured():
    test = parse(
        Args,
        "chocolate",
        "vanilla",
        "-p4",
    )
    assert test == Args(
        flavors=["chocolate", "vanilla"],
        something=4,
    )
