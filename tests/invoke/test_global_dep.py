from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cappa
from tests.utils import Backend, backends, invoke


def foo(command: Command):
    print("called", command)


def bar():
    print("two")


def command():
    return 1


@cappa.command(invoke=command)
@dataclass
class Command: ...


@backends
def test_invoke_global_dep(capsys: Any, backend: Backend):
    result = invoke(Command, deps=[foo, bar], backend=backend)
    assert result == 1

    out = capsys.readouterr().out
    assert "called Command()" in out
    assert "two" in out


@backends
def test_invoke_global_dep_string_reference(capsys: Any, backend: Backend):
    result = invoke(Command, deps=["tests.invoke.test_global_dep.foo"], backend=backend)
    assert result == 1

    out = capsys.readouterr().out
    assert "called Command()" in out
