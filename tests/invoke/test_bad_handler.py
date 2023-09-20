from __future__ import annotations

from dataclasses import dataclass

import cappa
import pytest

from tests.utils import invoke


def test_missing_invoke():
    @cappa.command()
    @dataclass
    class Command:
        ...

    with pytest.raises(ValueError) as e:
        invoke(Command)

    match = f"Cannot call `invoke` for a command which does not have an invoke handler: {Command}."
    assert str(e.value) == match


def test_string_missing_function():
    @cappa.command(invoke="sys")
    @dataclass
    class Command:
        ...

    with pytest.raises(ValueError, match="must be a fully qualified"):
        invoke(Command)


def test_string_references_invalid_module():
    @cappa.command(invoke="builtins.meow")
    @dataclass
    class Command:
        ...

    with pytest.raises(
        AttributeError, match="Module.*builtins.*does not have a function `meow`"
    ):
        invoke(Command)


def test_string_reference_not_callable():
    @cappa.command(invoke="builtins.__name__")
    @dataclass
    class Command:
        ...

    with pytest.raises(ValueError, match="does not reference a valid callable"):
        invoke(Command)
