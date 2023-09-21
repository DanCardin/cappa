from __future__ import annotations

from dataclasses import dataclass

import cappa
import pytest

from tests.utils import parse


def test_default_help(capsys):
    @dataclass
    class Command:
        """Some help.

        More detail.
        """

        ...

    with pytest.raises(ValueError):
        parse(Command, "--help")

    stdout = capsys.readouterr().out
    assert "\nSome help. More detail.\n" in stdout


def test_default_help_no_long_description(capsys):
    @dataclass
    class Command:
        """Some help."""

        ...

    with pytest.raises(ValueError):
        parse(Command, "--help")

    stdout = capsys.readouterr().out
    assert "\nSome help.\n" in stdout


def test_unannotated_argument(capsys):
    @cappa.command(help="All the help.")
    @dataclass
    class Command:
        ...

    with pytest.raises(ValueError):
        parse(Command, "--help")

    stdout = capsys.readouterr().out
    assert "\nAll the help.\n" in stdout


def test_description_without_help(capsys):
    @cappa.command(description="All the help.")
    @dataclass
    class Command:
        pass

    with pytest.raises(ValueError):
        parse(Command, "--help")

    stdout = capsys.readouterr().out
    assert "All the help.\n" in stdout
