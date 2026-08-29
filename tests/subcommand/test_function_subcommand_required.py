from __future__ import annotations

from typing import Any

import pytest

import cappa
from cappa.output import Exit
from tests.utils import Backend, backends, invoke, strip_trailing_whitespace


@cappa.command(name="add", help="Add two numbers.")
def add(a: float, b: float) -> float:
    return a + b


@cappa.command(name="subtract", help="Subtract b from a.")
def subtract(a: float, b: float) -> float:
    return a - b


@cappa.command(name="multiply", help="Multiply two numbers.")
def multiply(a: float, b: float) -> float:
    return a * b


@cappa.command(
    name="calc",
    help="Simple calculator.",
    subcommands=[add, subtract, multiply],
)
def calc(verbose: bool = False) -> None:
    if verbose:
        print("verbose")


@backends
def test_invoke_add(backend: Backend):
    assert invoke(calc, "add", "3", "4", backend=backend) == 7.0


@backends
def test_invoke_subtract(backend: Backend):
    assert invoke(calc, "subtract", "10", "3", backend=backend) == 7.0


@backends
def test_invoke_multiply(backend: Backend):
    assert invoke(calc, "multiply", "6", "7", backend=backend) == 42.0


@backends
def test_parent_arg_coexists(backend: Backend):
    assert invoke(calc, "--verbose", "add", "1", "2", backend=backend) == 3.0


@backends
def test_subcommand_required(backend: Backend):
    with pytest.raises(Exit) as exc:
        invoke(calc, backend=backend)
    msg = str(exc.value.message)
    assert "required" in msg
    assert "add" in msg
    assert "subtract" in msg
    assert "multiply" in msg


@backends
def test_help_lists_subcommands(backend: Backend, capsys: Any):
    with pytest.raises(Exit):
        invoke(calc, "--help", backend=backend)
    out = strip_trailing_whitespace(capsys.readouterr().out)
    assert "add" in out
    assert "subtract" in out
    assert "multiply" in out
    assert "Add two numbers" in out
