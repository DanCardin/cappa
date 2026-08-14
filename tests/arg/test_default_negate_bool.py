from __future__ import annotations

from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends, parse


@backends
def test_bool_gets_negate_form(backend: Backend):
    @cappa.command(default_negate_bool=True)
    @dataclass
    class Command:
        verbose: bool = False

    test = parse(Command, backend=backend)
    assert test.verbose is False

    test = parse(Command, "--verbose", backend=backend)
    assert test.verbose is True

    test = parse(Command, "--no-verbose", backend=backend)
    assert test.verbose is False


@backends
def test_bool_default_true_negate(backend: Backend):
    @cappa.command(default_negate_bool=True)
    @dataclass
    class Command:
        verbose: bool = True

    test = parse(Command, backend=backend)
    assert test.verbose is True

    test = parse(Command, "--verbose", backend=backend)
    assert test.verbose is True

    test = parse(Command, "--no-verbose", backend=backend)
    assert test.verbose is False


@backends
def test_non_bool_unaffected(backend: Backend):
    @cappa.command(default_negate_bool=True, default_long=True)
    @dataclass
    class Command:
        count: int = 0

    test = parse(Command, backend=backend)
    assert test.count == 0

    test = parse(Command, "--count", "5", backend=backend)
    assert test.count == 5

    with pytest.raises(cappa.Exit) as e:
        parse(Command, "--no-count", backend=backend)
    assert e.value.code == 2


@backends
def test_explicit_long_not_overridden(backend: Backend):
    @cappa.command(default_negate_bool=True)
    @dataclass
    class Command:
        verbose: Annotated[bool, cappa.Arg(long="--meow")] = False

    test = parse(Command, "--meow", backend=backend)
    assert test.verbose is True

    with pytest.raises(cappa.Exit) as e:
        parse(Command, "--no-verbose", backend=backend)
    assert e.value.code == 2


@backends
def test_mixed_bool_and_non_bool(backend: Backend):
    @cappa.command(default_negate_bool=True, default_long=True)
    @dataclass
    class Command:
        verbose: bool = False
        count: int = 0

    test = parse(Command, "--verbose", "--count", "3", backend=backend)
    assert test == Command(verbose=True, count=3)

    test = parse(Command, "--no-verbose", "--count", "1", backend=backend)
    assert test == Command(verbose=False, count=1)


@backends
def test_without_default_negate_bool_no_negate_form(backend: Backend):
    @cappa.command()
    @dataclass
    class Command:
        verbose: bool = False

    test = parse(Command, "--verbose", backend=backend)
    assert test.verbose is True

    with pytest.raises(cappa.Exit) as e:
        parse(Command, "--no-verbose", backend=backend)
    assert e.value.code == 2


@dataclass
class DestructuredArgs:
    verbose: bool = False
    dry_run: bool = True


@cappa.command(default_negate_bool=True)
@dataclass
class DestructuredCommand:
    args: cappa.Destructured[DestructuredArgs]


def test_destructured_propagates():
    test = parse(DestructuredCommand)
    assert test == DestructuredCommand(DestructuredArgs(verbose=False, dry_run=True))

    test = parse(DestructuredCommand, "--verbose", "--no-dry-run")
    assert test == DestructuredCommand(DestructuredArgs(verbose=True, dry_run=False))

    test = parse(DestructuredCommand, "--no-verbose", "--dry-run")
    assert test == DestructuredCommand(DestructuredArgs(verbose=False, dry_run=True))
