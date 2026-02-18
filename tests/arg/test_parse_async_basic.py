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
    value: Annotated[int, cappa.Arg(parse=async_parse_multiply)]


@backends
def test(backend: Backend):
    result = asyncio.run(cappa.parse_async(Command, argv=["5"], backend=backend))
    assert result.value == 10
