from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends, parse


@backends
def test_negative_int_option(backend: Backend):
    @dataclass
    class Args:
        count: Annotated[int, cappa.Arg(long=True)]

    result = parse(Args, "--count", "-5", backend=backend)
    assert result == Args(count=-5)


@backends
def test_negative_float_option(backend: Backend):
    @dataclass
    class Args:
        value: Annotated[float, cappa.Arg(long=True)]

    result = parse(Args, "--value", "-3.14", backend=backend)
    assert result == Args(value=-3.14)


@backends
def test_negative_int_short_option(backend: Backend):
    @dataclass
    class Args:
        count: Annotated[int, cappa.Arg(short=True)]

    result = parse(Args, "-c", "-10", backend=backend)
    assert result == Args(count=-10)
