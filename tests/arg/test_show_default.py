from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import pytest
from typing_extensions import Annotated

import cappa
from cappa.default import DefaultFormatter
from tests.utils import Backend, CapsysOutput, backends, parse


@backends
def test_show_default_default_true(backend: Backend, capsys: Any):
    @dataclass
    class Command:
        foo: bool = False

    assert parse(Command, backend=backend).foo is False

    with pytest.raises(cappa.HelpExit):
        parse(Command, "--help", backend=backend)

    output = CapsysOutput.from_capsys(capsys)
    assert "(Default: False)" in output.stdout


@backends
def test_show_default_set_false(backend: Backend, capsys: Any):
    @dataclass
    class Command:
        foo: Annotated[bool, cappa.Arg(show_default=False)] = False

    assert parse(Command, backend=backend).foo is False

    with pytest.raises(cappa.HelpExit):
        parse(Command, "--help", backend=backend)

    output = CapsysOutput.from_capsys(capsys)
    assert "(Default: False)" not in output.stdout


@backends
def test_show_default_no_option_shows_for_false_default(backend: Backend, capsys: Any):
    @dataclass
    class Command:
        foo: Annotated[bool, cappa.Arg(long="--foo/--no-foo")] = False

    assert parse(Command, backend=backend).foo is False

    with pytest.raises(cappa.HelpExit):
        parse(Command, "--help", backend=backend)

    stdout = CapsysOutput.from_capsys(capsys).stdout.replace(" ", "")
    assert "[--foo](Default:True)" not in stdout
    assert "[--no-foo](Default:False)" in stdout


@backends
def test_show_default_no_option_shows_for_true_default(backend: Backend, capsys: Any):
    @dataclass
    class Command:
        foo: Annotated[bool, cappa.Arg(long="--foo/--no-foo")] = True

    assert parse(Command, backend=backend).foo is True

    with pytest.raises(cappa.HelpExit):
        parse(Command, "--help", backend=backend)

    stdout = CapsysOutput.from_capsys(capsys).stdout.replace(" ", "")
    assert "[--foo](Default:True)" in stdout
    assert "[--no-foo](Default:False)" not in stdout


@backends
def test_show_default_string(backend: Backend, capsys: Any):
    @dataclass
    class Command:
        foo: Annotated[str, cappa.Arg(show_default="~{default}~")] = "asdf"

    with pytest.raises(cappa.HelpExit):
        parse(Command, "--help", backend=backend)

    stdout = CapsysOutput.from_capsys(capsys).stdout.replace(" ", "")
    assert "[FOO](Default:~asdf~)" in stdout


@backends
def test_show_default_explicit(backend: Backend, capsys: Any):
    @dataclass
    class Command:
        foo: Annotated[str, cappa.Arg(show_default=DefaultFormatter("!{default}!"))] = (
            "asdf"
        )

    with pytest.raises(cappa.HelpExit):
        parse(Command, "--help", backend=backend)

    stdout = CapsysOutput.from_capsys(capsys).stdout.replace(" ", "")
    assert "[FOO](Default:!asdf!)" in stdout


@backends
def test_static(backend: Backend, capsys: Any):
    @dataclass
    class Command:
        foo: Annotated[str | None, cappa.Arg(show_default="always show")] = None

    with pytest.raises(cappa.HelpExit):
        parse(Command, "--help", backend=backend)

    stdout = CapsysOutput.from_capsys(capsys).stdout
    assert re.search(r"\[FOO\]\s+\(Default: always show\)", stdout)
