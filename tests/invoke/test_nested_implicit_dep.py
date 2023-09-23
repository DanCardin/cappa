from __future__ import annotations

from dataclasses import dataclass
from typing import Union

import cappa
from typing_extensions import Annotated

from tests.utils import invoke


def foo(tlc: TopLevelCommand, subcommand: Subcommand, foo: Foo):
    return (tlc, subcommand, foo)


@cappa.command(invoke=foo)
@dataclass
class Foo:
    ...


@dataclass
class Subcommand:
    cmd: Annotated[Foo, cappa.Subcommand]


@cappa.command(invoke=lambda: 4)
@dataclass
class TopLevelCommand:
    cmd: Annotated[Union[Subcommand, None], cappa.Subcommand] = None


def test_every_dependency_level():
    result = invoke(TopLevelCommand, "subcommand", "foo")
    assert result == (
        TopLevelCommand(cmd=Subcommand(cmd=Foo())),
        Subcommand(cmd=Foo()),
        Foo(),
    )


def test_no_subcmd():
    result = invoke(TopLevelCommand)
    assert result == 4
