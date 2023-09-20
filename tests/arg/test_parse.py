from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import cappa

from tests.utils import parse


def split(value: str):
    a, b = value.split(",", 1)
    return int(a), int(b)


def test_explicit_parse_function():
    @dataclass
    class ArgTest:
        numbers: Annotated[int, cappa.Arg(parse=int)]

    test = parse(ArgTest, "1")
    assert test.numbers == 1


def test_not_typeable_parse_function():
    @dataclass
    class ArgTest:
        numbers: Annotated[tuple[int, int], cappa.Arg(parse=split)]

    test = parse(ArgTest, "1,3")
    assert test.numbers == (1, 3)
