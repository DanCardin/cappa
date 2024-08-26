from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@backends
def test_short_missing_dash(backend):
    @dataclass
    class ArgTest:
        number: Annotated[int, cappa.Arg(short="n")]

    result = parse(ArgTest, "-n", "4", backend=backend)
    assert result.number == 4


@backends
def test_multiple_shorts(backend):
    @dataclass
    class ArgTest:
        number: Annotated[int, cappa.Arg(short=["n", "o"])]

    result = parse(ArgTest, "-n", "4", backend=backend)
    assert result.number == 4

    result = parse(ArgTest, "-o", "4", backend=backend)
    assert result.number == 4


@backends
def test_long_missing_dash(backend):
    @dataclass
    class ArgTest:
        number: Annotated[int, cappa.Arg(long="nu")]

    result = parse(ArgTest, "--nu", "4", backend=backend)
    assert result.number == 4


@backends
def test_multiple_longs(backend):
    @dataclass
    class ArgTest:
        number: Annotated[int, cappa.Arg(long=["so", "long"])]

    result = parse(ArgTest, "--so", "4", backend=backend)
    assert result.number == 4

    result = parse(ArgTest, "--long", "4", backend=backend)
    assert result.number == 4
