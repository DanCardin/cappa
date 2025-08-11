from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import parse


@dataclass
class CollisionSub:
    field1: str = ""
    field2: Annotated[str, cappa.Arg(long=True)] = ""


@dataclass
class Collision:
    sub: cappa.Destructured[CollisionSub]
    field1: int = 0
    field2: int = 0


def test_destructured_collision():
    result = parse(Collision, "1")
    assert result == Collision(sub=CollisionSub("1", ""), field1=0)

    result = parse(Collision, "1", "2")
    assert result == Collision(sub=CollisionSub("1", ""), field1=2)

    result = parse(Collision, "--field2=-1", "1", "2", "3")
    assert result == Collision(sub=CollisionSub("1", "-1"), field1=2, field2=3)
