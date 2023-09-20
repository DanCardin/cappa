from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class ArgTest:
    name: tuple[Literal["one"], str] | tuple[Literal["two"], int] | tuple[
        Literal["three"],
        float,
    ]


# def test_str():
#     test = parse(ArgTest, "one", "string")
#     assert test.name == ("one", "string")
#
#
# def test_int():
#     test = parse(ArgTest, "two", "4")
#     assert test.name == ("two", 4)
#
#
# def test_float():
#     test = parse(ArgTest, "three", "1.4")
#     assert test.name == ("three", 1.4)
