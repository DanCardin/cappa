from dataclasses import dataclass

import cappa
import pytest

from tests.utils import backends


@backends
def test_invoke_exit_success_with_message(capsys, backend):
    def fn():
        raise cappa.Exit("With message")

    @cappa.command(invoke=fn)
    @dataclass
    class Example:
        ...

    with pytest.raises(cappa.Exit):
        cappa.invoke(Example, argv=[""], backend=backend)

    out = capsys.readouterr().out
    assert out == "With message\n"


@backends
def test_invoke_exit_success_without_message(capsys, backend):
    def fn():
        raise cappa.Exit()

    @cappa.command(invoke=fn)
    @dataclass
    class Example:
        ...

    with pytest.raises(cappa.Exit):
        cappa.invoke(Example, argv=[""], backend=backend)

    out = capsys.readouterr().out
    assert out == ""


@backends
def test_invoke_exit_errror(capsys, backend):
    def fn():
        raise cappa.Exit("With message", code=1)

    @cappa.command(invoke=fn)
    @dataclass
    class Example:
        ...

    with pytest.raises(cappa.Exit) as e:
        cappa.invoke(Example, argv=[""], backend=backend)

    assert e.value.code == 1
    out = capsys.readouterr().err
    assert out == "With message\n"
