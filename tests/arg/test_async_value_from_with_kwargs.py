from __future__ import annotations

import asyncio
from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from cappa.default import ValueFrom
from tests.utils import Backend, backends


async def async_value_with_kwargs(multiplier: int) -> int:
    await asyncio.sleep(0.001)
    return 10 * multiplier


@dataclass
class Command:
    value: Annotated[
        int, cappa.Arg(default=ValueFrom(async_value_with_kwargs, multiplier=5))
    ]

    def __call__(self):
        return self


@backends
def test(backend: Backend):
    result = asyncio.run(cappa.invoke_async(Command, argv=[], backend=backend))
    assert result.value == 50
