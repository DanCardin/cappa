from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends, parse


@backends
def test_negative_int_positional(backend: Backend):
    @dataclass
    class Args:
        value: int

    result = parse(Args, "-5", backend=backend)
    assert result == Args(value=-5)


@backends
def test_negative_float_positional(backend: Backend):
    @dataclass
    class Args:
        value: float

    result = parse(Args, "-2.718", backend=backend)
    assert result == Args(value=-2.718)


@backends
def test_negative_positional_with_option(backend: Backend):
    @dataclass
    class Args:
        verbose: Annotated[bool, cappa.Arg(short=True, default=False)]
        value: int

    result = parse(Args, "-v", "-42", backend=backend)
    assert result == Args(verbose=True, value=-42)
