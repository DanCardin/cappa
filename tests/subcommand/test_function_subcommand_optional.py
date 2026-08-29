from __future__ import annotations

import cappa
from tests.utils import Backend, backends, invoke


@cappa.command(name="add", help="Add two numbers.")
def add(a: float, b: float) -> float:
    return a + b


@cappa.command(name="calc", subcommands=[add, None])
def calc(verbose: bool = False) -> bool:
    return verbose


@backends
def test_invoke_add(backend: Backend):
    assert invoke(calc, "add", "3", "4", backend=backend) == 7.0


@backends
def test_invoke_calc(backend: Backend):
    assert invoke(calc, backend=backend) is False


@backends
def test_invoke_calc_verbose(backend: Backend):
    assert invoke(calc, "--verbose", backend=backend) is True
