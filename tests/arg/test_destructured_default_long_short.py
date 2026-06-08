from __future__ import annotations

from dataclasses import dataclass

import cappa
from tests.utils import parse


@dataclass
class Args:
    foo: int = 4
    bar: int = 5


@cappa.command(default_long=True, default_short=True)
@dataclass
class Command:
    args: cappa.Destructured[Args]


@cappa.command(default_long=True)
@dataclass
class InnerOverrideArgs:
    foo: int = 4


@cappa.command(default_long=False)
@dataclass
class InnerOverrideCommand:
    args: cappa.Destructured[InnerOverrideArgs]


def test_default_long_propagates():
    test = parse(Command, "--foo", "1", "--bar", "2")
    assert test == Command(Args(1, 2))


def test_default_short_propagates():
    test = parse(Command, "-f", "1", "-b", "2")
    assert test == Command(Args(1, 2))


def test_inner_command_setting_takes_precedence():
    test = parse(InnerOverrideCommand, "--foo", "1")
    assert test == InnerOverrideCommand(InnerOverrideArgs(1))
