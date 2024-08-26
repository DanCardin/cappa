# type: ignore
from __future__ import annotations

import attr
from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse

factory = attr.Factory(lambda: [4])


@attr.s
class Command:
    name: str = attr.ib()
    default: Annotated[int, cappa.Arg(long=True)] = attr.ib(default=4)
    default_factory: Annotated[list[int], cappa.Arg(long=True)] = attr.ib(
        default=factory
    )


@backends
def test_attrs(backend):
    result = parse(Command, "meow", backend=backend)
    assert result == Command(name="meow", default=4, default_factory=[4])
