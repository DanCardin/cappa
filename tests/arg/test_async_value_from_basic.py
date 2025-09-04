from __future__ import annotations

import asyncio
from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from cappa.default import ValueFrom
from tests.utils import Backend, backends


async def async_value_provider() -> int:
    await asyncio.sleep(0.001)
    return 42


@dataclass
class Command:
    value: Annotated[int, cappa.Arg(default=ValueFrom(async_value_provider))]

    def __call__(self):
        return self


@backends
def test(backend: Backend):
    result = asyncio.run(cappa.invoke_async(Command, argv=[], backend=backend))
    assert result.value == 42

    result = asyncio.run(cappa.invoke_async(Command, argv=["123"], backend=backend))
    assert result.value == 123
