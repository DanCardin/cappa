from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Any

import cappa
from tests.utils import Backend, backends


@dataclass
class Command:
    value: str = "test"
    closed: bool = False

    def __enter__(self):
        return self

    def __exit__(self, *args: Any):
        object.__setattr__(self, "closed", True)


@backends
def test(backend: Backend):
    with contextlib.ExitStack() as stack:
        result = cappa.parse(Command, argv=[], backend=backend, exit_stack=stack)

        assert not result.closed
        assert result.value == "test"

    assert result.closed
