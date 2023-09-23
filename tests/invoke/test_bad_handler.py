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

    with pytest.raises(RuntimeError) as e:
        invoke(Command)

    exc = e.value
    cause = exc.__cause__
    assert "due to resolution failure" in str(exc)
    assert (
        f"Cannot call `invoke` for a command which does not have an invoke handler: {Command}."
        == str(cause)
    )


def test_string_missing_function():
    @cappa.command(invoke="sys")
    @dataclass
    class Command:
        ...

    with pytest.raises(RuntimeError) as e:
        invoke(Command)

    exc = e.value
    cause = exc.__cause__
    assert "due to resolution failure" in str(exc)
    assert (
        "Invoke `sys` must be a fully qualified reference to a function in a module."
        == str(cause)
    )


def test_string_references_invalid_module():
    @cappa.command(invoke="completely.wrong")
    @dataclass
    class Command:
        ...

    with pytest.raises(RuntimeError) as e:
        invoke(Command)

    exc = e.value
    cause = exc.__cause__
    assert "due to resolution failure" in str(exc)
    assert "No module 'completely' when attempting to load 'completely.wrong'." == str(
        cause
    )


def test_string_references_invalid_function():
    @cappa.command(invoke="builtins.meow")
    @dataclass
    class Command:
        ...

    with pytest.raises(RuntimeError) as e:
        invoke(Command)

    exc = e.value
    cause = exc.__cause__
    assert "due to resolution failure" in str(exc)
    assert (
        "Module <module 'builtins' (built-in)> does not have a function `meow`."
        == str(cause)
    )


def test_string_reference_not_callable():
    @cappa.command(invoke="builtins.__name__")
    @dataclass
    class Command:
        ...

    with pytest.raises(RuntimeError) as e:
        invoke(Command)

    exc = e.value
    cause = exc.__cause__
    assert "due to resolution failure" in str(exc)
    assert "`builtins` does not reference a valid callable." == str(cause)
