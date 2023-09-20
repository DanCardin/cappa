from __future__ import annotations

from dataclasses import dataclass

import cappa
import pytest

from tests.utils import invoke


def test_invalid_dependency():
    def command(levels: int):
        return levels

    @cappa.command(invoke=command)
    @dataclass
    class Command:
        ...

    with pytest.raises(RuntimeError, match=r"`levels: int` is not a valid dependency"):
        invoke(Command)


def test_unannotated_argument():
    def command(levels):
        return levels

    @cappa.command(invoke=command)
    @dataclass
    class Command:
        ...

    with pytest.raises(
        RuntimeError, match=r"`levels: <empty>` is not a valid dependency"
    ):
        invoke(Command)
