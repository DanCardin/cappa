from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import pytest

import cappa
from cappa.output import Exit
from tests.utils import Backend, backends, parse


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
