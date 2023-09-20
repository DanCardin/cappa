from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import cappa

from tests.utils import parse


def test_short_missing_dash():
    @dataclass
    class ArgTest:
        number: Annotated[int, cappa.Arg(short="nu")]

    result = parse(ArgTest, "-nu", "4")
    assert result.number == 4


def test_long_missing_dash():
    @dataclass
    class ArgTest:
        number: Annotated[int, cappa.Arg(long="nu")]

    result = parse(ArgTest, "--nu", "4")
    assert result.number == 4
