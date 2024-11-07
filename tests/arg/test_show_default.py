from __future__ import annotations

from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import CapsysOutput, backends, parse


@backends
def test_show_default_default_true(backend, capsys):
    @dataclass
    class Command:
        foo: bool = False

    assert parse(Command, backend=backend).foo is False

    with pytest.raises(cappa.HelpExit):
        parse(Command, "--help", backend=backend)

    output = CapsysOutput.from_capsys(capsys)
    assert "(Default: False)" in output.stdout


@backends
def test_show_default_set_false(backend, capsys):
    @dataclass
    class Command:
        foo: Annotated[bool, cappa.Arg(show_default=False)] = False

    assert parse(Command, backend=backend).foo is False

    with pytest.raises(cappa.HelpExit):
        parse(Command, "--help", backend=backend)

    output = CapsysOutput.from_capsys(capsys)
    assert "(Default: False)" not in output.stdout


@backends
def test_show_default_no_option_shows_for_false_default(backend, capsys):
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
def test_show_default_no_option_shows_for_true_default(backend, capsys):
    @dataclass
    class Command:
        foo: Annotated[bool, cappa.Arg(long="--foo/--no-foo")] = True

    assert parse(Command, backend=backend).foo is True

    with pytest.raises(cappa.HelpExit):
        parse(Command, "--help", backend=backend)

    stdout = CapsysOutput.from_capsys(capsys).stdout.replace(" ", "")
    assert "[--foo](Default:True)" in stdout
    assert "[--no-foo](Default:False)" not in stdout
