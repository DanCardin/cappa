from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import backends, invoke


def two():
    return 2


def three(_: Command):
    return 3


def one(two: Annotated[int, cappa.Dep(two)], three: Annotated[int, cappa.Dep(three)]):
    return (two, three)


def command(one: Annotated[int, cappa.Dep(one)]):
    return one


@cappa.command(invoke=command)
@dataclass
class Command: ...


@backends
def test_invoke_top_level_command(backend):
    def stub_two():
        return 4

    result = invoke(Command, deps={two: cappa.Dep(stub_two), three: 6}, backend=backend)
    assert result == (4, 6)
