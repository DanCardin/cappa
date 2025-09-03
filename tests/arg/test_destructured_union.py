from __future__ import annotations

from dataclasses import dataclass

import pytest

import cappa
from tests.utils import parse


@dataclass
class Foo:
    foo: int


@dataclass
class CLI:
    attrs: cappa.Destructured[Foo | int]


def test_destructured_union():
    with pytest.raises(ValueError) as e:
        parse(CLI)
    assert (
        str(e.value)
        == "Destructured arguments currently only support singular concrete types."
    )
