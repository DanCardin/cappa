from __future__ import annotations

from dataclasses import dataclass

import pytest

import cappa
from tests.utils import Backend, backends, invoke


@backends
def test_invalid_dependency(backend: Backend):
    def command(levels: int):
        return levels

    @cappa.command(invoke=command)
    @dataclass
    class Command: ...

    with pytest.raises(RuntimeError) as e:
        invoke(Command, backend=backend)

    exc = e.value
    cause = exc.__cause__
    assert "due to resolution failure" in str(exc)
    assert "`levels: int` is not a valid dependency for Dep(command)." == str(cause)


@backends
def test_unannotated_argument(backend: Backend):
    def command(levels):  # pyright: ignore
        return levels  # pyright: ignore

    @cappa.command(invoke=command)  # pyright: ignore
    @dataclass
    class Command: ...

    with pytest.raises(RuntimeError) as e:
        invoke(Command, backend=backend)

    exc = e.value
    cause = exc.__cause__
    assert "due to resolution failure" in str(exc)
    assert "`levels: <empty>` is not a valid dependency for Dep(command)." == str(cause)
