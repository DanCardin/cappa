from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pytest

from tests.utils import parse


@dataclass
class ArgTest:
    name: int | Literal["one"]


def test_valid_int():
    test = parse(ArgTest, "5")
    assert test.name == 5


def test_valid_literal():
    test = parse(ArgTest, "one")
    assert test.name == "one"


def test_invalid_string():
    with pytest.raises(
        ValueError,
        match=r"Could not parse 'thename' given options: <int>, one",
    ):
        parse(ArgTest, "thename")
