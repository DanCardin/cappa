from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import cappa

from tests.utils import invoke


def top_level_command(tlc: TopLevelCommand):
    return ("tlc", tlc)


def sub_command(sub: Subcommand):
    return ("sub", sub)


@cappa.command(name="sub", invoke=sub_command)
@dataclass
class Subcommand:
    bar: int


@cappa.command(invoke=top_level_command)
@dataclass
class TopLevelCommand:
    foo: Annotated[int, cappa.Arg(long=True)] = 4
    subcommand: Annotated[Subcommand | None, cappa.Subcommand] = None


def test_invoke_top_level_command():
    result = invoke(TopLevelCommand, "--foo", "4")
    assert result == ("tlc", TopLevelCommand(foo=4))


def test_invoke_subcommand():
    result = invoke(TopLevelCommand, "sub", "4")
    assert result == ("sub", Subcommand(bar=4))
