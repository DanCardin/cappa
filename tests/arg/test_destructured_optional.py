from __future__ import annotations

from dataclasses import dataclass

import cappa
from tests.utils import parse


@dataclass
class Foo:
    foo: int = 4


@dataclass
class CLI:
    attrs: cappa.Destructured[Foo | None] = None


def test_destructured_optional():
    result = parse(CLI)
    assert result == CLI(attrs=None)
