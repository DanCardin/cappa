from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from cappa.default import ValueFrom
from tests.utils import Backend, backends


async def async_value_that_fails():
    await asyncio.sleep(0.001)
    raise RuntimeError("Async fetch failed")


@dataclass
class Command:
    value: Annotated[int, cappa.Arg(default=ValueFrom(async_value_that_fails))]

    def __call__(self):
        return self


@backends
def test(backend: Backend):
    with pytest.raises(RuntimeError, match="Async fetch failed"):
        asyncio.run(cappa.invoke_async(Command, argv=[], backend=backend))
