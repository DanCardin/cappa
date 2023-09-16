from __future__ import annotations

import enum
from dataclasses import dataclass

import pytest

from tests.utils import parse


class Options(enum.Enum):
    one = "one"
    two = "two"
    three = "three"


@dataclass
class ArgTest:
    options: Options


@pytest.mark.xfail()
def test_valid():
    test = parse(ArgTest, "two")
    assert test.name == "two"


@pytest.mark.xfail()
def test_invalid():
    with pytest.raises(
        ValueError, match="Could not map 'thename' given options: one, two, three"
    ):
        parse(ArgTest, "thename")
