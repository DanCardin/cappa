from __future__ import annotations

import asyncio
from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends


async def async_fetch_raw_value() -> str:
    await asyncio.sleep(0.001)
    return "10"


async def async_parse_multiply(value: str) -> int:
    await asyncio.sleep(0.001)
    return int(value) * 2


@dataclass
class Command:
    value: Annotated[
        int,
        cappa.Arg(
            default=cappa.ValueFrom(async_fetch_raw_value),
            parse=async_parse_multiply,
        ),
    ]

    def __call__(self):
        return self


@backends
def test(backend: Backend):
    # ValueFrom returns is_parsed=True, so parse is NOT applied
    result = asyncio.run(cappa.invoke_async(Command, argv=[], backend=backend))
    assert result.value == "10"

    # With explicit value: parse IS applied
    result = asyncio.run(cappa.invoke_async(Command, argv=["5"], backend=backend))
    assert result.value == 10
