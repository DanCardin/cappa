from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# from tests.utils import parse, backends


@dataclass
class ArgTest:
    name: tuple[Literal["one"], str] | tuple[Literal["two"], int] | tuple[
        Literal["three"],
        float,
    ]


# @backends
# def test_str(backend):
#     test = parse(ArgTest, "one", "string", backend=backend)
#     assert test.name == ("one", "string")
#
#
# @backends
# def test_int(backend):
#     test = parse(ArgTest, "two", "4", backend=backend)
#     assert test.name == ("two", 4)
#
#
# @backends
# def test_float(backend):
#     test = parse(ArgTest, "three", "1.4", backend=backend)
#     assert test.name == ("three", 1.4)
