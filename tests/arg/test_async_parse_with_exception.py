from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends


async def async_parse_that_fails(value: str) -> int:
    await asyncio.sleep(0.001)
    raise ValueError("Async parsing failed")


@dataclass
class Command:
    value: Annotated[int, cappa.Arg(parse=async_parse_that_fails)]

    def __call__(self):
        return self


@backends
def test(backend: Backend):
    with pytest.raises(cappa.Exit) as exc_info:
        asyncio.run(cappa.invoke_async(Command, argv=["42"], backend=backend))

    assert exc_info.value.code == 2
    assert "Async parsing failed" in str(exc_info.value.message)
