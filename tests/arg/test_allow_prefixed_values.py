from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import List

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import CapsysOutput, parse


@dataclass
class Command:
    foo: Annotated[
        str | None, cappa.Arg(long=True, short=True, allow_prefixed_values=True)
    ] = None
    bar: Annotated[str | None, cappa.Arg(long=True)] = None
    flag: Annotated[bool, cappa.Arg(short="-x")] = False


def test_long_option_value():
    assert parse(Command, "--foo", "--bar") == Command(foo="--bar")


def test_short_option_value():
    assert parse(Command, "-f", "-x") == Command(foo="-x")


def test_explicit_value_unchanged():
    assert parse(Command, "--foo=--bar") == Command(foo="--bar")


def test_normal_value_unchanged():
    assert parse(Command, "--foo", "val", "-x") == Command(foo="val", flag=True)


def test_other_options_still_parse():
    assert parse(Command, "--foo", "--bar", "--bar", "1") == Command(
        foo="--bar", bar="1"
    )


def test_not_enabled_by_default(capsys: pytest.CaptureFixture[str]):
    with pytest.raises(cappa.Exit) as e:
        parse(Command, "--bar", "--foo")
    assert e.value.code == 2
    assert "requires an argument" in CapsysOutput.from_capsys(capsys).stderr


def test_double_dash_not_a_value():
    @dataclass
    class Cmd:
        foo: Annotated[str, cappa.Arg(long=True, allow_prefixed_values=True)]
        rest: Annotated[List[str], cappa.Arg(num_args=-1)]

    assert parse(Cmd, "--foo", "-x", "--", "--a") == Cmd(foo="-x", rest=["--a"])


def test_multiple_values():
    @dataclass
    class Cmd:
        foo: Annotated[
            List[str],
            cappa.Arg(long=True, num_args=2, allow_prefixed_values=True),
        ]

    assert parse(Cmd, "--foo", "-a", "--b") == Cmd(foo=["-a", "--b"])


def test_positional_invalid():
    @dataclass
    class Cmd:
        foo: Annotated[str, cappa.Arg(allow_prefixed_values=True)]

    with pytest.raises(ValueError, match="allow_prefixed_values"):
        parse(Cmd, "a")


def test_double_dash_not_consumed_as_pending_value():
    @dataclass
    class Cmd:
        foo: Annotated[
            str | None,
            cappa.Arg(
                long=True,
                num_args=cappa.NumArgs(required=False),
                allow_prefixed_values=True,
            ),
        ] = None
        rest: Annotated[List[str], cappa.Arg(num_args=-1)] = dataclasses.field(
            default_factory=lambda: []
        )

    assert parse(Cmd, "--foo", "--", "a") == Cmd(foo=None, rest=["a"])
