from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import parse


@dataclass
class Items:
    items: Annotated[list[str], cappa.Arg(long=True, action=cappa.ArgAction.append)] = (
        dataclasses.field(default_factory=lambda: [])
    )


@dataclass
class Args:
    w: cappa.Destructured[Items]


def test_append_multiple():
    result = parse(Args, "--items=a", "--items=b", "--items=c")
    assert result == Args(w=Items(items=["a", "b", "c"]))


def test_append_default_empty():
    result = parse(Args)
    assert result == Args(w=Items(items=[]))
