from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import cappa
import pytest

from tests.utils import parse


@dataclass
class Command:
    subcmd: Annotated[A | None, cappa.Subcommand(required=True)] = None


@dataclass
class A:
    ...


def test_required_implicit():
    with pytest.raises(ValueError, match=r"are required: {a}"):
        parse(Command)

    result = parse(Command, "a")
    assert result == Command(subcmd=A())
