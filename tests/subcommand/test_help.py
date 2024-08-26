from __future__ import annotations

import textwrap
from dataclasses import dataclass

import pytest

import cappa
from tests.utils import parse, strip_trailing_whitespace


@dataclass
class Sub:
    arg: str


@dataclass
class Args:
    command: cappa.Subcommands[Sub]


def test_required_arg_subcommand_help(capsys):
    """Assert short help is emitted for the subcommand (on bad input) rather than the root help."""
    with pytest.raises(cappa.Exit) as e:
        parse(Args, "sub")

    assert e.value.code == 2
    out = strip_trailing_whitespace(capsys.readouterr().err)

    assert out == textwrap.dedent(
        """\
        Usage: args sub ARG [-h]

        Error: Option 'arg' requires an argument
        """
    )
