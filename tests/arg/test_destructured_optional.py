from __future__ import annotations

from dataclasses import dataclass

import pytest

import cappa
from tests.utils import parse


@dataclass
class Foo:
    foo: int


@dataclass
class OptionalArgs:
    attrs: cappa.Destructured[Foo | None]


def test_destructured_optional():
    with pytest.raises(ValueError) as e:
        parse(OptionalArgs)
    assert (
        str(e.value)
        == "Destructured arguments currently only support singular concrete types."
    )
