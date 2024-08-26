from __future__ import annotations

import typing
from dataclasses import dataclass

import cappa
from tests.utils import backends, parse


@dataclass
class Command:
    cmd: cappa.Subcommands[typing.Union[Foo, Bar]]


@dataclass
class Foo:
    f: int


@dataclass
class Bar:
    b: int


@backends
def test_subcommand_type_type_alias(backend):
    result = parse(Command, "foo", "4", backend=backend)
    assert result == Command(cmd=Foo(f=4))

    result = parse(Command, "bar", "4", backend=backend)
    assert result == Command(cmd=Bar(b=4))
