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


def called():
    return ["42"]


@backends
def test_positional_unbound_num_args(backend):
    @dataclass
    class Command:
        positional: Annotated[
            list[str],
            cappa.Arg(
                short=False,
                long=False,
                default=cappa.ValueFrom(called),
            ),
        ]

    result = parse(Command, "7", backend=backend)
    assert result == Command(["7"])

    result = parse(Command, backend=backend)
    assert result == Command(["42"])


def two_tuple():
    return ("42", "0")


def test_optional_positional_2_tuple():
    @dataclass
    class Command:
        positional: Annotated[
            tuple[str, str],
            cappa.Arg(
                short=False,
                long=False,
                default=cappa.ValueFrom(two_tuple),
            ),
        ]

    result = parse(Command, "7", "8")
    assert result == Command(("7", "8"))

    result = parse(Command)
    assert result == Command(("42", "0"))
