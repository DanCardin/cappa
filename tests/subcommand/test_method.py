from __future__ import annotations

from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from cappa.output import Exit
from tests.utils import backends, invoke, parse, strip_trailing_whitespace


def some_dep():
    return 5


@cappa.command
@dataclass
class HasExecutableMethods:
    arg: int
    include_dep: bool = False

    @cappa.command
    def add(self, some_dep: Annotated[int, cappa.Dep(some_dep)]) -> int:
        """Add two numbers."""
        if self.add:
            return self.arg + some_dep
        return self.arg

    @cappa.command(help="Subtract two numbers")
    def subtract(self, other: int) -> int:
        if self.add:
            return self.arg - other
        return self.arg


@backends
def test_parse(backend):
    result = parse(HasExecutableMethods, "10", "add", backend=backend)
    assert result == HasExecutableMethods(10, False)

    result = parse(HasExecutableMethods, "10", "subtract", "2", backend=backend)
    assert result == HasExecutableMethods(10, False)

    result = parse(HasExecutableMethods, "11", "--include-dep", "add", backend=backend)
    assert result == HasExecutableMethods(11, True)

    result = parse(
        HasExecutableMethods, "11", "--include-dep", "subtract", "2", backend=backend
    )
    assert result == HasExecutableMethods(11, True)

    with pytest.raises(Exit) as e:
        parse(HasExecutableMethods, "10", backend=backend)
    message = str(e.value.message)
    assert "required" in message
    assert "add" in message
    assert "subtract" in message


@backends
def test_invoke_add(backend):
    result = invoke(HasExecutableMethods, "10", "add", backend=backend)
    assert result == 15

    with pytest.raises(Exit) as e:
        invoke(HasExecutableMethods, "10", backend=backend)
    message = str(e.value.message)
    assert "required" in message
    assert "add" in message
    assert "subtract" in message


@backends
def test_invoke_subtract(backend):
    result = invoke(HasExecutableMethods, "10", "subtract", "7", backend=backend)
    assert result == 3

    with pytest.raises(Exit) as e:
        invoke(HasExecutableMethods, "10", backend=backend)
    message = str(e.value.message)
    assert "required" in message
    assert "add" in message
    assert "subtract" in message


@backends
def test_help(backend, capsys):
    with pytest.raises(Exit):
        invoke(HasExecutableMethods, "--help", backend=backend)

    out = strip_trailing_whitespace(capsys.readouterr().out)
    assert "Add two numbers" in out
    assert "Subtract two numbers" in out


@backends
def test_nested_method_invalid_ast_source(backend, capsys):
    @cappa.command
    @dataclass
    class Example:
        @cappa.command
        def add(self): ...

    with pytest.raises(Exit):
        invoke(Example, "--help", backend=backend)

    out = strip_trailing_whitespace(capsys.readouterr().out)
    assert "add" in out
