from __future__ import annotations

import asyncio
from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends


def sync_parse_lowercase(value: str) -> str:
    return value.lower()


async def async_parse_uppercase(value: str) -> str:
    await asyncio.sleep(0.001)
    return value.upper()


@dataclass
class Command:
    sync_value: Annotated[str, cappa.Arg(parse=sync_parse_lowercase)]
    async_value: Annotated[str, cappa.Arg(parse=async_parse_uppercase)]

    def __call__(self):
        return self


@backends
def test(backend: Backend):
    result = asyncio.run(
        cappa.invoke_async(Command, argv=["HELLO", "world"], backend=backend)
    )
    assert result.sync_value == "hello"
    assert result.async_value == "WORLD"
