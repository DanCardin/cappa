from dataclasses import dataclass, field
from typing import Any, ClassVar

import pytest

import cappa
from cappa.command import Command
from tests.utils import Backend, backends


@backends
def test_color_off(backend: Backend):
    def no_op():
        pass

    @cappa.command(invoke=no_op)
    @dataclass
    class Example: ...

    cappa.invoke(Example, color=False, argv=[], backend=backend)


@backends
def test_no_help(backend: Backend):
    @dataclass
    class Example: ...

    result = cappa.parse(Example, argv=[], help=False, backend=backend)
    assert result == Example()

    with pytest.raises(SystemExit) as e:
        cappa.parse(Example, argv=["-h"], help=False, backend=backend)
    assert e.value.code == 2

    with pytest.raises(SystemExit) as e:
        cappa.parse(Example, argv=["--help"], help=False, backend=backend)
    assert e.value.code == 2


@pytest.mark.help
@backends
def test_arg_help(capsys: Any, backend: Backend):
    @dataclass
    class Example: ...

    help: cappa.Arg[str] = cappa.Arg(short="-p", long="--pelp")

    result = cappa.parse(Example, argv=[], help=help, backend=backend)
    assert result == Example()

    with pytest.raises(SystemExit) as e:
        cappa.parse(Example, argv=["-p"], help=help, backend=backend)
    assert e.value.code == 0

    out = capsys.readouterr().out
    assert "-p, --pelp" in out

    with pytest.raises(SystemExit) as e:
        cappa.parse(Example, argv=["--pelp"], help=help, backend=backend)
    assert e.value.code == 0

    out = capsys.readouterr().out
    assert "-p, --pelp" in out


@backends
def test_version_enabled(capsys: Any, backend: Backend):
    @dataclass
    class Example: ...

    with pytest.raises(SystemExit) as e:
        cappa.parse(Example, argv=["--version"], version="1.2.3", backend=backend)
    assert e.value.code == 0

    out = capsys.readouterr().out
    assert "1.2.3" in out


@backends
def test_arg_version(capsys: Any, backend: Backend):
    @dataclass
    class Example: ...

    version: cappa.Arg[str] = cappa.Arg("1.2.3", short="-p", long="--persion")

    result = cappa.parse(Example, argv=[], version=version, backend=backend)
    assert result == Example()

    with pytest.raises(SystemExit) as e:
        cappa.parse(Example, argv=["-p"], version=version, backend=backend)
    assert e.value.code == 0

    out = capsys.readouterr().out
    assert "1.2.3" in out

    with pytest.raises(SystemExit) as e:
        cappa.parse(Example, argv=["--persion"], version=version, backend=backend)
    assert e.value.code == 0

    out = capsys.readouterr().out
    assert "1.2.3" in out


@backends
def test_version_without_help(backend: Backend):
    @dataclass
    class Example: ...

    result = cappa.parse(Example, argv=[], version="1.2.3", help=False, backend=backend)
    assert result == Example()


@backends
def test_arg_explicit_version_missing_name(backend: Backend):
    @dataclass
    class Example: ...

    version: cappa.Arg[str] = cappa.Arg(short="-p", long="--persion")

    with pytest.raises(ValueError) as e:
        cappa.parse(Example, argv=["-p"], version=version, backend=backend)

    assert (
        str(e.value)
        == "Expected explicit version `Arg` to supply version number as its name, like `Arg('1.2.3', ...)`"
    )


@backends
def test_arg_explicit_version_long_true_defaults_to_version(
    capsys: Any, backend: Backend
):
    @dataclass
    class Example: ...

    version: cappa.Arg[str] = cappa.Arg("1.2.3", short="-p", long=True)

    with pytest.raises(cappa.Exit):
        cappa.parse(Example, argv=["--version"], version=version, backend=backend)

    out = capsys.readouterr().out
    assert "1.2.3" in out


@backends
def test_prog_basename(capsys: Any, backend: Backend):
    @dataclass
    class Example: ...

    with pytest.raises(cappa.Exit):
        cappa.parse(Example, argv=["--help"], backend=backend)

    out = capsys.readouterr().out
    assert "usage: example" in out.lower()


@backends
def test_collect_composes_with_parse(backend: Backend):
    @dataclass
    class Example: ...

    command: Command[Example] = cappa.collect(Example, backend=backend)
    result = cappa.parse(command, argv=[], backend=backend)

    assert result == Example()


@backends
def test_collect_skips_non_init_fields(backend: Backend):
    @dataclass
    class Example:
        skipped1: ClassVar[str] = "skipped1"
        skipped2: str = field(default="", init=False)
        present: str = ""

    command: Command[Example] = cappa.collect(Example, backend=backend)
    result = cappa.parse(command, argv=[], backend=backend)

    assert result == Example()
