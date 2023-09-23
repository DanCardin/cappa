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

    with pytest.raises(RuntimeError) as e:
        invoke(Command)

    exc = e.value
    cause = exc.__cause__
    assert "due to resolution failure" in str(exc)
    assert "`levels: int` is not a valid dependency for Dep(command)." == str(cause)


def test_unannotated_argument():
    def command(levels):
        return levels

    @cappa.command(invoke=command)
    @dataclass
    class Command:
        ...

    with pytest.raises(RuntimeError) as e:
        invoke(Command)

    exc = e.value
    cause = exc.__cause__
    assert "due to resolution failure" in str(exc)
    assert "`levels: <empty>` is not a valid dependency for Dep(command)." == str(cause)
