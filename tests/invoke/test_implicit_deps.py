from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from typing_extensions import Annotated

import cappa
from tests.utils import backends, invoke


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
    subcommand: Annotated[Union[Subcommand, None], cappa.Subcommand] = None


@backends
def test_invoke_top_level_command(backend):
    result = invoke(TopLevelCommand, "--foo", "4", backend=backend)
    assert result == ("tlc", TopLevelCommand(foo=4))


@backends
def test_invoke_subcommand(backend):
    result = invoke(TopLevelCommand, "sub", "4", backend=backend)
    assert result == ("sub", Subcommand(bar=4))
