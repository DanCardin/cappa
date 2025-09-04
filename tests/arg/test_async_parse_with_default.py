from __future__ import annotations

import asyncio
from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends


async def async_parse_int(value: str) -> int:
    await asyncio.sleep(0.001)
    result = int(value)
    if result < 0:
        raise ValueError("Value must be non-negative")
    return result


@dataclass
class Command:
    value: Annotated[int, cappa.Arg(parse=async_parse_int, default=100)]

    def __call__(self):
        return self


@backends
def test(backend: Backend):
    result = asyncio.run(cappa.invoke_async(Command, argv=[], backend=backend))
    assert result.value == 100

    result = asyncio.run(cappa.invoke_async(Command, argv=["42"], backend=backend))
    assert result.value == 42
