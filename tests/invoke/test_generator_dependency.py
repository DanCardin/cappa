from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import backends, invoke

log = logging.getLogger("test")


def binary_io():
    print("binary before")
    with io.BytesIO() as buffer:
        yield buffer
    print("binary after")


def text_io(binary_io: Annotated[io.BytesIO, cappa.Dep(binary_io)]):
    print("text before")
    text_buffer = io.TextIOWrapper(binary_io)
    yield text_buffer
    print("text after")


def csv_file(text_io: Annotated[io.TextIOWrapper, cappa.Dep(text_io)]):
    print("csv before")
    writer = csv.DictWriter(text_io, ["foo", "bar"])
    writer.writeheader()
    writer.writerow({"foo": 1, "bar": "woah"})
    text_io.detach()
    yield writer
    print("csv after")


def command(
    _: Annotated[dict, cappa.Dep(csv_file)],
    binary_io: Annotated[io.BytesIO, cappa.Dep(binary_io)],
):
    assert not binary_io.closed
    return binary_io, binary_io.getvalue()


@cappa.command(invoke=command)
@dataclass
class Command: ...


@backends
def test_invoke_top_level_command(backend, capsys):
    buffer, result = invoke(Command, backend=backend)

    assert buffer.closed is True
    assert result == b"foo,bar\r\n1,woah\r\n"

    out = capsys.readouterr().out
    assert out == (
        "binary before\n"
        "text before\n"
        "csv before\n"
        "csv after\n"
        "text after\n"
        "binary after\n"
    )
