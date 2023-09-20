from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from tests.utils import parse


@dataclass
class ArgTest:
    numbers: Tuple[int, str, float]


def test_valid():
    test = parse(ArgTest, "1", "2", "3.4")
    assert test.numbers == (1, "2", 3.4)
