from __future__ import annotations

import asyncio
from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from cappa.default import ValueFrom
from tests.utils import Backend, backends


async def async_list_provider() -> list[str]:
    await asyncio.sleep(0.001)
    return ["async", "list", "values"]


@dataclass
class Command:
    values: Annotated[
        list[str],
        cappa.Arg(
            short=False,
            long=False,
            default=ValueFrom(async_list_provider),
        ),
    ]

    def __call__(self):
        return self


@backends
def test(backend: Backend):
    result = asyncio.run(cappa.invoke_async(Command, argv=[], backend=backend))
    assert result.values == ["async", "list", "values"]

    result = asyncio.run(cappa.invoke_async(Command, argv=["a", "b"], backend=backend))
    assert result.values == ["a", "b"]
