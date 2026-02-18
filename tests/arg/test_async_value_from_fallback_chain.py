from __future__ import annotations

import asyncio
from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from cappa.default import ValueFrom
from tests.utils import Backend, backends


async def async_fallback() -> int:
    await asyncio.sleep(0.001)
    return 99


@dataclass
class Command:
    value: Annotated[
        int, cappa.Arg(default=cappa.Env("MISSING_VAR") | ValueFrom(async_fallback))
    ]

    def __call__(self):
        return self


@backends
def test(backend: Backend):
    result = asyncio.run(cappa.invoke_async(Command, argv=[], backend=backend))
    assert result.value == 99
