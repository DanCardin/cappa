from __future__ import annotations

import contextlib
import io
from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends


@contextlib.contextmanager
def binary_io():
    with io.BytesIO() as buffer:
        yield buffer


def command(
    binary_io: Annotated[io.BytesIO, cappa.Dep(binary_io)],
):
    assert not binary_io.closed
    binary_io.write(b"hello from command")
    return binary_io


@cappa.command(invoke=command)
@dataclass
class Command:
    pass


@backends
def test(backend: Backend):
    buffer = cappa.invoke(Command, argv=[], backend=backend)
    assert buffer.closed
