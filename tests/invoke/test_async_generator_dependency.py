from __future__ import annotations

import asyncio
import csv
import io
import logging
from dataclasses import dataclass
from typing import Any

from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends, invoke_async

log = logging.getLogger("test")


async def binary_io():
    print("binary before")
    with io.BytesIO() as buffer:
        yield buffer
    print("binary after")


async def text_io(binary_io: Annotated[io.BytesIO, cappa.Dep(binary_io)]):
    print("text before")
    text_buffer = io.TextIOWrapper(binary_io)
    yield text_buffer
    print("text after")


async def csv_file(text_io: Annotated[io.TextIOWrapper, cappa.Dep(text_io)]):
    print("csv before")
    writer = csv.DictWriter(text_io, ["foo", "bar"])
    writer.writeheader()
    writer.writerow({"foo": 1, "bar": "woah"})
    text_io.detach()
    yield writer
    print("csv after")


def command(
    _: Annotated[dict[Any, Any], cappa.Dep(csv_file)],
    binary_io: Annotated[io.BytesIO, cappa.Dep(binary_io)],
):
    assert not binary_io.closed
    return binary_io, binary_io.getvalue()


@cappa.command(invoke=command)
@dataclass
class Command: ...


@backends
def test_invoke_top_level_command(backend: Backend, capsys: Any):
    buffer, result = asyncio.run(invoke_async(Command, backend=backend))

    assert buffer.closed is True
    assert result == b"foo,bar\r\n1,woah\r\n"

    out = capsys.readouterr().out
    assert out == (
        "binary before\ntext before\ncsv before\ncsv after\ntext after\nbinary after\n"
    )
