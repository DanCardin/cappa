from dataclasses import dataclass

import cappa
import pytest


def test_color_off():
    def no_op():
        pass

    @cappa.command(invoke=no_op)
    @dataclass
    class Example:
        ...

    cappa.invoke(Example, color=False, argv=[])


def test_no_help():
    @dataclass
    class Example:
        ...

    result = cappa.parse(Example, argv=[], help=False)
    assert result == Example()

    with pytest.raises(SystemExit):
        cappa.parse(Example, argv=["ex", "-h"], help=False)

    with pytest.raises(SystemExit):
        cappa.parse(Example, argv=["ex", "--help"], help=False)


def test_arg_help(capsys):
    @dataclass
    class Example:
        ...

    help: cappa.Arg = cappa.Arg(short="-p", long="--pelp")

    result = cappa.parse(Example, argv=[], help=help)
    assert result == Example()

    with pytest.raises(SystemExit):
        cappa.parse(Example, argv=["ex", "-p"], help=help)
    out = capsys.readouterr().out
    assert "-p, --pelp" in out

    with pytest.raises(SystemExit):
        cappa.parse(Example, argv=["ex", "--pelp"], help=help)
    out = capsys.readouterr().out
    assert "-p, --pelp" in out


def test_version_enabled(capsys):
    @dataclass
    class Example:
        ...

    with pytest.raises(SystemExit):
        cappa.parse(Example, argv=["ex", "--version"], version="1.2.3")
    out = capsys.readouterr().out
    assert "1.2.3" in out


def test_arg_version(capsys):
    @dataclass
    class Example:
        ...

    version: cappa.Arg = cappa.Arg("1.2.3", short="-p", long="--persion")

    result = cappa.parse(Example, argv=[], version=version)
    assert result == Example()

    with pytest.raises(SystemExit):
        cappa.parse(Example, argv=["ex", "-p"], version=version)
    out = capsys.readouterr().out
    assert "1.2.3" in out

    with pytest.raises(SystemExit):
        cappa.parse(Example, argv=["ex", "--persion"], version=version)
    out = capsys.readouterr().out
    assert "1.2.3" in out


def test_version_without_help(capsys):
    @dataclass
    class Example:
        ...

    result = cappa.parse(Example, argv=[], version="1.2.3", help=False)
    assert result == Example()
