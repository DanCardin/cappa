# type: ignore
from __future__ import annotations

from typing import List

import attr
import cappa
from typing_extensions import Annotated

from tests.utils import parse

factory = attr.Factory(lambda: [4])


@attr.s
class Command:
    name: str = attr.ib()
    default: Annotated[int, cappa.Arg(long=True)] = attr.ib(default=4)
    default_factory: Annotated[List[int], cappa.Arg(long=True)] = attr.ib(
        default=factory
    )


def test_attrs():
    result = parse(Command, "meow")
    assert result == Command(name="meow", default=4, default_factory=[4])
