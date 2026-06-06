from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

from typing_extensions import Annotated

import cappa
from cappa import Env, ValueFrom
from tests.utils import parse


@dataclass
class Foo:
    color: Annotated[str, cappa.Arg(long=True, default=Env("FOO"))]


@dataclass
class Args:
    attrs: cappa.Destructured[Foo]


def test_env_default_no_cli_arg():
    with patch("os.environ", new={"FOO": "blue"}):
        result = parse(Args)
    assert result == Args(attrs=Foo("blue"))


def test_env_default_cli_overrides():
    with patch("os.environ", new={"FOO": "blue"}):
        result = parse(Args, "--color=red")
    assert result == Args(attrs=Foo("red"))


@dataclass
class Bar:
    x: Annotated[int, cappa.Arg(long=True, default=Env("BAR_X"))]
    y: Annotated[str, cappa.Arg(long=True, default="fallback")]


@dataclass
class PartialArgs:
    bar: cappa.Destructured[Bar]


def test_partial_args_missing_field_uses_env():
    with patch("os.environ", new={"BAR_X": "42"}):
        result = parse(PartialArgs, "--y=hello")
    assert result == PartialArgs(bar=Bar(x=42, y="hello"))


def test_partial_args_all_from_env_and_default():
    with patch("os.environ", new={"BAR_X": "7"}):
        result = parse(PartialArgs)
    assert result == PartialArgs(bar=Bar(x=7, y="fallback"))


@dataclass
class Baz:
    val: Annotated[int, cappa.Arg(long=True, default=ValueFrom(lambda: 99))]


@dataclass
class ValueFromArgs:
    baz: cappa.Destructured[Baz]


def test_value_from_default():
    result = parse(ValueFromArgs)
    assert result == ValueFromArgs(baz=Baz(val=99))
