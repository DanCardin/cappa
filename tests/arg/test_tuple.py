from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from tests.utils import backends, parse


@dataclass
class ArgTest:
    numbers: Tuple[int, str, float]


@backends
def test_valid(backend):
    test = parse(ArgTest, "1", "2", "3.4", backend=backend)
    assert test.numbers == (1, "2", 3.4)
