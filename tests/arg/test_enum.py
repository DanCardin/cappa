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


def test_valid():
    test = parse(ArgTest, "two")
    assert test.options is Options.two


def test_invalid():
    with pytest.raises(
        ValueError,
        match=r"argument options: invalid choice: 'thename' \(choose from 'one', 'two', 'three'\)",
    ):
        parse(ArgTest, "thename")
