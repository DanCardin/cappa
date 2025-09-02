from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import parse


@dataclass
class Other:
    arg2: Annotated[int, cappa.Arg(long=True)] = 4
    arg3: Annotated[str, cappa.Arg(long=True)] = "value3"


@dataclass
class CLI:
    other: cappa.Destructured[Other]


def test_destructured_implicit_default():
    result = parse(CLI)
    assert result == CLI(other=Other())


@dataclass
class OptionalCLI:
    other: cappa.Destructured[Other | None]


def test_destructured_implicit_default_optional_annotation():
    result = parse(OptionalCLI)
    assert result == OptionalCLI(other=None)
