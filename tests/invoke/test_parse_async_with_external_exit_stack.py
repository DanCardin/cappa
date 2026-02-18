from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from typing import Any

import cappa
from tests.utils import Backend, backends


@dataclass
class Command:
    value: str = "test"
    closed: bool = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args: Any):
        object.__setattr__(self, "closed", True)


@backends
def test(backend: Backend):
    async def run_test():
        async with contextlib.AsyncExitStack() as stack:
            result = await cappa.parse_async(
                Command, argv=[], backend=backend, exit_stack=stack
            )

            assert not result.closed
            assert result.value == "test"

            return result

    result = asyncio.run(run_test())
    assert result.closed
