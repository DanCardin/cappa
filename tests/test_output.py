from dataclasses import dataclass

import cappa
import pytest


def test_with_rich(capsys):
    cappa.print("test", rich=True)

    out = capsys.readouterr().err
    assert out == "test\n"


@pytest.mark.parametrize("flush", (True, False))
def test_without_rich(capsys, flush):
    cappa.print("test", rich=False, flush=flush)

    out = capsys.readouterr().err
    assert out == "test\n"


def test_invoke_exit_success_with_message(capsys):
    def fn():
        raise cappa.Exit("With message")

    @cappa.command(invoke=fn)
    @dataclass
    class Example:
        ...

    with pytest.raises(cappa.Exit):
        cappa.invoke(Example, argv=[""])

    out = capsys.readouterr().err
    assert out == "With message\n"


def test_invoke_exit_success_without_message(capsys):
    def fn():
        raise cappa.Exit()

    @cappa.command(invoke=fn)
    @dataclass
    class Example:
        ...

    with pytest.raises(cappa.Exit):
        cappa.invoke(Example, argv=[""])

    out = capsys.readouterr().err
    assert out == ""


def test_invoke_exit_errror():
    def fn():
        raise cappa.Exit("With message", code=1)

    @cappa.command(invoke=fn)
    @dataclass
    class Example:
        ...

    with pytest.raises(cappa.Exit) as e:
        cappa.invoke(Example, argv=[""])

    assert e.value.code == 1
