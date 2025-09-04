from __future__ import annotations

import asyncio
from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from cappa.default import ValueFrom
from tests.utils import Backend, backends


async def async_value_with_deps(state: cappa.State[dict[str, str]]) -> str:
    await asyncio.sleep(0.001)
    return f"state-value-{state.get('key', default='default')}"


@dataclass
class Command:
    value: Annotated[str, cappa.Arg(default=ValueFrom(async_value_with_deps))]

    def __call__(self):
        return self


@backends
def test(backend: Backend):
    state: cappa.State[dict[str, str]] = cappa.State()
    state.set("key", "injected")

    result = asyncio.run(
        cappa.invoke_async(Command, argv=[], backend=backend, state=state)
    )
    assert result.value == "state-value-injected"
