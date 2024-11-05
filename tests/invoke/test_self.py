from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import backends, invoke


def foo(command: cappa.Self[HasDefault]):
    print(f"called with {command.default}")


@dataclass
class HasDefault:
    default: Annotated[int, cappa.Arg(short=True)] = 1

    def __call__(self):
        return 2


@dataclass
class Command(HasDefault):
    sub: cappa.Subcommands[Foo | Bar | None] = None


@dataclass
class Foo(HasDefault):
    default: Annotated[int, cappa.Arg(short=True)] = 2


@dataclass
class Bar(HasDefault):
    default: Annotated[int, cappa.Arg(short=True)] = 3


@backends
def test_typing_self(capsys, backend):
    invoke(Command, deps=[foo], backend=backend)
    out = capsys.readouterr().out
    assert "called with 1" in out

    invoke(Command, "foo", deps=[foo], backend=backend)
    out = capsys.readouterr().out
    assert "called with 2" in out

    invoke(Command, "bar", deps=[foo], backend=backend)
    out = capsys.readouterr().out
    assert "called with 3" in out
