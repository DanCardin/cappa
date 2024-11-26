from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import pytest
from typing_extensions import Annotated

import cappa
from cappa.default import ValueFrom
from tests.utils import backends, parse


def woah(value):
    return 1 + value


@dataclass
class Command:
    foo: Annotated[int, cappa.Arg(default=cappa.Env("FOO"))] = 4
    bar: Annotated[
        int, cappa.Arg(default=cappa.Env("BAR") | ValueFrom(woah, value=4))
    ] = 0


@backends
def test_valid(backend):
    result = parse(Command, "6", "7", backend=backend)
    assert result == Command(6, 7)

    result = parse(Command, backend=backend)
    assert result == Command(4, 5)

    with patch("os.environ", new={"FOO": "3", "BAR": "9"}):
        result = parse(Command, backend=backend)
        assert result == Command(3, 9)


def raises():
    raise ValueError()


@backends
def test_not_parsed(backend):
    @dataclass
    class Command:
        foo: Annotated[int, cappa.Arg(parse=raises, default=ValueFrom(int))]

    with pytest.raises(cappa.Exit):
        parse(Command, "7", backend=backend)

    result = parse(Command, backend=backend)
    assert result == Command(0)
