from __future__ import annotations

from dataclasses import dataclass

import cappa
from typing_extensions import Annotated

from tests.utils import parse


def test_short_missing_dash():
    @dataclass
    class ArgTest:
        number: Annotated[int, cappa.Arg(short="nu")]

    result = parse(ArgTest, "-nu", "4")
    assert result.number == 4


def test_multiple_shorts():
    @dataclass
    class ArgTest:
        number: Annotated[int, cappa.Arg(short=["n", "o"])]

    result = parse(ArgTest, "-n", "4")
    assert result.number == 4

    result = parse(ArgTest, "-o", "4")
    assert result.number == 4


def test_long_missing_dash():
    @dataclass
    class ArgTest:
        number: Annotated[int, cappa.Arg(long="nu")]

    result = parse(ArgTest, "--nu", "4")
    assert result.number == 4


def test_multiple_longs():
    @dataclass
    class ArgTest:
        number: Annotated[int, cappa.Arg(long=["so", "long"])]

    result = parse(ArgTest, "--so", "4")
    assert result.number == 4

    result = parse(ArgTest, "--long", "4")
    assert result.number == 4
