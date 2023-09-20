from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Literal

import pytest

from tests.utils import parse


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires 3.10")
def test_valid():
    @dataclass
    class ArgTest:
        name: Literal["one"] | Literal["two"] | Literal["three"] | Literal[4]

    test = parse(ArgTest, "two")
    assert test.name == "two"
