from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from typing_extensions import Annotated

import cappa
from tests.utils import backends, invoke


def foo(tlc: TopLevelCommand, subcommand: Subcommand, foo: Foo):
    return (tlc, subcommand, foo)


@cappa.command(invoke=foo)
@dataclass
class Foo: ...


@dataclass
class Subcommand:
    cmd: Annotated[Foo, cappa.Subcommand]


@cappa.command(invoke=lambda: 4)
@dataclass
class TopLevelCommand:
    cmd: Annotated[Union[Subcommand, None], cappa.Subcommand] = None


@backends
def test_every_dependency_level(backend):
    result = invoke(TopLevelCommand, "subcommand", "foo", backend=backend)
    assert result == (
        TopLevelCommand(cmd=Subcommand(cmd=Foo())),
        Subcommand(cmd=Foo()),
        Foo(),
    )


@backends
def test_no_subcmd(backend):
    result = invoke(TopLevelCommand, backend=backend)
    assert result == 4
