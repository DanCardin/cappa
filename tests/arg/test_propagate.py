from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from typing_extensions import Annotated

import cappa
from cappa.subcommand import Subcommands
from tests.utils import CapsysOutput, parse


@dataclass
class Command:
    foo: Annotated[int, cappa.Arg(long=True, propagate=True, help="Everywhere")] = 1
    sub: cappa.Subcommands[One | Two | None] = None


@dataclass
class One: ...


@dataclass
class Two: ...


def test_propagated_arg():
    result = parse(Command)
    assert result == Command(1, None)

    result = parse(Command, "--foo=4")
    assert result == Command(4, None)

    result = parse(Command, "one", "--foo=5")
    assert result == Command(5, One())

    result = parse(Command, "two", "--foo=6")
    assert result == Command(6, Two())


def test_propagate_incompatible_with_argparse():
    with pytest.raises(RuntimeError):
        parse(Command, backend=cappa.argparse.backend)


@dataclass
class Required:
    foo: Annotated[int, cappa.Arg(long=True, propagate=True)]
    sub: cappa.Subcommands[One | Two | None] = None


def test_required_propagated_arg():
    with pytest.raises(cappa.Exit):
        parse(Required)

    result = parse(Required, "--foo=4")
    assert result == Required(4, None)

    result = parse(Required, "one", "--foo=5")
    assert result == Required(5, One())

    result = parse(Required, "two", "--foo=6")
    assert result == Required(6, Two())


@dataclass
class ChildOverride:
    foo: Annotated[int, cappa.Arg(long=True, propagate=True)] = 1
    sub: cappa.Subcommands[Child | None] = None


@dataclass
class Child:
    foo: Annotated[int, cappa.Arg(long=True)] = 2


def test_child_override():
    result = parse(ChildOverride)
    assert result == ChildOverride(1, None)

    result = parse(ChildOverride, "--foo=4")
    assert result == ChildOverride(4, None)

    result = parse(ChildOverride, "--foo=4", "child")
    assert result == ChildOverride(4, Child(2))

    result = parse(ChildOverride, "child")
    assert result == ChildOverride(1, Child(2))

    result = parse(ChildOverride, "child", "--foo=5")
    assert result == ChildOverride(1, Child(5))

    result = parse(ChildOverride, "--foo=3", "child", "--foo=6")
    assert result == ChildOverride(3, Child(6))


def test_propagate_requires_option():
    @dataclass
    class ChildOverride:
        foo: Annotated[int, cappa.Arg(propagate=True)]

    with pytest.raises(ValueError) as e:
        parse(ChildOverride)
    assert (
        str(e.value)
        == "`Arg.propagate` requires a non-positional named option (`short` or `long`)."
    )


def test_help_contains_propagated_arg(capsys: Any):
    @dataclass
    class Command:
        foo: Annotated[int, cappa.Arg(long=True, propagate=True, help="Everywhere")] = 1
        bar: Annotated[int, cappa.Arg(long=True, help="Nowhere")] = 1
        sub: cappa.Subcommands[One | Two | None] = None

    with pytest.raises(cappa.Exit):
        parse(Command, "--help")
    output = CapsysOutput.from_capsys(capsys)
    assert "foo" in output.stdout
    assert "Everywhere" in output.stdout
    assert "Nowhere" in output.stdout

    with pytest.raises(cappa.Exit):
        parse(Command, "one", "--help")
    output = CapsysOutput.from_capsys(capsys)
    assert "foo" in output.stdout
    assert "Everywhere" in output.stdout
    assert "Nowhere" not in output.stdout

    with pytest.raises(cappa.Exit):
        parse(Command, "two", "--help")
    output = CapsysOutput.from_capsys(capsys)
    assert "foo" in output.stdout
    assert "Everywhere" in output.stdout
    assert "Nowhere" not in output.stdout


def test_count():
    """Test that actions requiring accumulated prior state (e.g. count) **get** values from the correct context."""

    @dataclass
    class Command:
        foo: Annotated[int, cappa.Arg(short=True, propagate=True, count=True)] = 1
        subcommand: Subcommands[One | None] = None

    result = parse(Command, "-f")
    assert result == Command(1, None)

    result = parse(Command, "-fff")
    assert result == Command(3, None)

    result = parse(Command, "one", "-f")
    assert result == Command(1, One())

    result = parse(Command, "one", "-fff")
    assert result == Command(3, One())
