from __future__ import annotations

from dataclasses import dataclass

import cappa
from typing_extensions import Annotated

from tests.utils import invoke


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
class Command:
    ...


def test_invoke_top_level_command():
    def stub_two():
        return 4

    result = invoke(Command, deps={two: cappa.Dep(stub_two), three: 6})
    assert result == (4, 6)
