from __future__ import annotations

import asyncio
from contextlib import contextmanager
from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends, invoke_async


@contextmanager
def sync_dep():
    yield 42


async def async_handler(value: Annotated[int, cappa.Dep(sync_dep)]):
    return value * 2


@cappa.command(invoke=async_handler)
@dataclass
class AsyncCommandWithSyncDep: ...


@backends
def test_invoke_async_with_sync_dep(backend: Backend):
    """Test that invoke_async works with a synchronous dependency."""
    result = asyncio.run(invoke_async(AsyncCommandWithSyncDep, backend=backend))
    assert result == 84
