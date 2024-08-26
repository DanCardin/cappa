from __future__ import annotations

import re
from dataclasses import dataclass

import pytest

import cappa
from cappa.output import Exit
from tests.utils import backends, parse


@pytest.mark.help
@backends
def test_default_help(backend, capsys):
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
def test_default_help_no_long_description(backend, capsys):
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
def test_unannotated_argument(backend, capsys):
    @cappa.command(help="All the help.")
    @dataclass
    class Command: ...

    with pytest.raises(Exit):
        parse(Command, "--help", backend=backend)

    stdout = capsys.readouterr().out
    assert "All the help." in stdout


@pytest.mark.help
@backends
def test_description_without_help(backend, capsys):
    @cappa.command(description="All the help.")
    @dataclass
    class Command:
        pass

    with pytest.raises(Exit):
        parse(Command, "--help", backend=backend)

    stdout = capsys.readouterr().out
    assert "All the help." in stdout
