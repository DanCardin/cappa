from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@dataclass
class Command:
    foo: Annotated[int, cappa.Arg(default=4)]
    bar: Annotated[int, cappa.Arg(default=5)]


@backends
def test_valid(backend):
    test = parse(Command, "1", "2", backend=backend)
    assert test == Command(1, 2)


@backends
def test_default_is_not_mapped(backend):
    @dataclass
    class Command:
        foo: int = "4"  # type: ignore

    test = parse(Command, "1", backend=backend)
    assert test == Command(1)

    test = parse(Command, backend=backend)
    assert test == Command("4")  # type: ignore
