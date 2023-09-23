from __future__ import annotations

from dataclasses import dataclass

import cappa

from tests.utils import invoke


def foo(command: Command):
    print("called", command)


def bar():
    print("two")


def command():
    return 1


@cappa.command(invoke=command)
@dataclass
class Command:
    ...


def test_invoke_top_level_command(capsys):
    result = invoke(Command, deps=[foo, bar])
    assert result == 1

    out = capsys.readouterr().out
    assert "called Command()" in out
    assert "two" in out
