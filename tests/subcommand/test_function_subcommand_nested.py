from __future__ import annotations

import cappa
from tests.utils import Backend, backends, invoke


@cappa.command(name="two")
def two(a: float, b: float) -> float:
    return a + b


@cappa.command(name="three")
def three(a: float, b: float, c: float) -> float:
    return a + b + c


@cappa.command(name="add", subcommands=[two, three, None])
def add() -> float:
    return 4


@cappa.command(name="calc", subcommands=[add, None])
def calc(verbose: bool = False) -> bool:
    return verbose


@backends
def test_invoke_add_none(backend: Backend):
    assert invoke(calc, "--verbose", "add", backend=backend) == 4.0


@backends
def test_invoke_add_two(backend: Backend):
    assert invoke(calc, "--verbose", "add", "two", "3", "4", backend=backend) == 7.0


@backends
def test_invoke_add_three(backend: Backend):
    assert (
        invoke(calc, "--verbose", "add", "three", "3", "4", "3", backend=backend)
        == 10.0
    )
