from __future__ import annotations

from dataclasses import dataclass

import pytest

import cappa
from tests.utils import backends, invoke


@backends
def test_missing_invoke(backend):
    @cappa.command()
    @dataclass
    class Command: ...

    with pytest.raises(RuntimeError) as e:
        invoke(Command, backend=backend)

    exc = e.value
    cause = exc.__cause__
    assert "due to resolution failure" in str(exc)
    assert (
        f"Cannot call `invoke` for a command which does not have an invoke handler: {Command}."
        == str(cause)
    )


@backends
def test_string_missing_function(backend):
    @cappa.command(invoke="sys")
    @dataclass
    class Command: ...

    with pytest.raises(RuntimeError) as e:
        invoke(Command, backend=backend)

    exc = e.value
    cause = exc.__cause__
    assert "due to resolution failure" in str(exc)
    assert (
        "Invoke `sys` must be a fully qualified reference to a function in a module."
        == str(cause)
    )


@backends
def test_string_references_invalid_module(backend):
    @cappa.command(invoke="completely.wrong")
    @dataclass
    class Command: ...

    with pytest.raises(RuntimeError) as e:
        invoke(Command, backend=backend)

    exc = e.value
    cause = exc.__cause__
    assert "due to resolution failure" in str(exc)
    assert "No module 'completely' when attempting to load 'completely.wrong'." == str(
        cause
    )


@backends
def test_string_references_invalid_function(backend):
    @cappa.command(invoke="builtins.meow")
    @dataclass
    class Command: ...

    with pytest.raises(RuntimeError) as e:
        invoke(Command, backend=backend)

    exc = e.value
    cause = exc.__cause__
    assert "due to resolution failure" in str(exc)
    assert (
        "Module <module 'builtins' (built-in)> does not have a function `meow`."
        == str(cause)
    )


@backends
def test_string_reference_not_callable(backend):
    @cappa.command(invoke="builtins.__name__")
    @dataclass
    class Command: ...

    with pytest.raises(RuntimeError) as e:
        invoke(Command, backend=backend)

    exc = e.value
    cause = exc.__cause__
    assert "due to resolution failure" in str(exc)
    assert "`builtins` does not reference a valid callable." == str(cause)
