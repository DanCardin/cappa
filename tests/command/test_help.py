from __future__ import annotations

import re
from dataclasses import dataclass
from textwrap import dedent
from typing import Any

import pytest

import cappa
from cappa.output import Exit
from tests.utils import (
    Backend,
    backends,
    parse,
    strip_trailing_whitespace,
    terminal_width,
)


@pytest.mark.help
@backends
def test_default_help(backend: Backend, capsys: Any):
    @dataclass
    class Command:
        """Some help.

        More detail.
        """

        ...

    with pytest.raises(Exit):
        parse(Command, "--help", backend=backend)

    stdout = capsys.readouterr().out
    assert re.match(r".*Some help\.\s+More detail\..*", stdout, re.DOTALL)


@pytest.mark.help
@backends
def test_default_help_no_long_description(backend: Backend, capsys: Any):
    @dataclass
    class Command:
        """Some help."""

        ...

    with pytest.raises(Exit):
        parse(Command, "--help", backend=backend)

    stdout = capsys.readouterr().out
    assert "Some help." in stdout


@pytest.mark.help
@backends
def test_unannotated_argument(backend: Backend, capsys: Any):
    @cappa.command(help="All the help.")
    @dataclass
    class Command: ...

    with pytest.raises(Exit):
        parse(Command, "--help", backend=backend)

    stdout = capsys.readouterr().out
    assert "All the help." in stdout


@pytest.mark.help
@backends
def test_description_without_help(backend: Backend, capsys: Any):
    @cappa.command(description="All the help.")
    @dataclass
    class Command:
        pass

    with pytest.raises(Exit):
        parse(Command, "--help", backend=backend)

    stdout = capsys.readouterr().out
    assert "All the help." in stdout


@pytest.mark.help
@backends
def test_epilog(backend: Backend, capsys: Any):
    @cappa.command(epilog="See also: https://example.com")
    @dataclass
    class Command:
        pass

    with terminal_width(), pytest.raises(Exit):
        parse(Command, "--help", backend=backend, completion=False)

    result = strip_trailing_whitespace(capsys.readouterr().out)
    tail = result[result.index("[-h, --help]") :]
    assert tail == dedent(
        """\
        [-h, --help]  Show this message and exit.


          See also: https://example.com
        """
    )
