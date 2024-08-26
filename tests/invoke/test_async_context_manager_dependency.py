from __future__ import annotations

import asyncio
import contextlib
import io
import logging
from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import backends, invoke_async

log = logging.getLogger("test")


@contextlib.asynccontextmanager
async def binary_io():
    with io.BytesIO() as buffer:
        yield buffer


def command(
    binary_io: Annotated[io.BytesIO, cappa.Dep(binary_io)],
):
    assert not binary_io.closed
    binary_io.write(b"hello")
    return binary_io, binary_io.getvalue()


@cappa.command(invoke=command)
@dataclass
class Command: ...


@backends
def test_invoke_top_level_command(backend):
    buffer, result = asyncio.run(invoke_async(Command, backend=backend))

    assert buffer.closed is True
    assert result == b"hello"
