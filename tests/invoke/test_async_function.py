from __future__ import annotations

import asyncio
from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import backends, invoke_async


def bar():
    return 7


async def foo(bar: Annotated[int, cappa.Dep(bar)]):
    return bar + 9


async def handler(foo: Annotated[int, cappa.Dep(foo)]):
    return foo + 1


@cappa.command(invoke=handler)
@dataclass
class Command: ...


def idk():
    print("wat")


@backends
def test_async_fn(backend, capsys):
    result = asyncio.run(invoke_async(Command, backend=backend, deps=[idk]))
    assert result == 7 + 9 + 1

    assert capsys.readouterr().out == "wat\n"
