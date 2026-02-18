from __future__ import annotations

import asyncio
from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends


async def async_parse_multiply(value: str) -> int:
    await asyncio.sleep(0.001)
    return int(value) * 2


@dataclass
class Command:
    value: Annotated[int | None, cappa.Arg(long=True, parse=async_parse_multiply)] = (
        None
    )

    def __call__(self):
        return self


@backends
def test(backend: Backend):
    result = asyncio.run(cappa.invoke_async(Command, argv=[], backend=backend))
    assert result.value is None

    result = asyncio.run(
        cappa.invoke_async(Command, argv=["--value", "10"], backend=backend)
    )
    assert result.value == 20
