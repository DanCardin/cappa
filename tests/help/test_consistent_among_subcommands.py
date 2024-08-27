from __future__ import annotations

from dataclasses import dataclass

import pytest

import cappa
from tests.utils import parse


@dataclass
class SubTwo: ...


@dataclass
class SubOne:
    sub_two: cappa.Subcommands[SubTwo]


@dataclass
class Args:
    sub_one: cappa.Subcommands[SubOne]


def test_all_help_options_share_defined_help_argument(capsys):
    help: cappa.Arg = cappa.Arg(help="this is custom text", long=True)

    with pytest.raises(cappa.HelpExit):
        parse(Args, "--help", help=help)
    out = capsys.readouterr().out
    assert "this is custom text" in out

    with pytest.raises(cappa.HelpExit):
        parse(Args, "sub-one", "--help", help=help)
    out = capsys.readouterr().out
    assert "this is custom text" in out

    with pytest.raises(cappa.HelpExit):
        parse(Args, "sub-one", "sub-two", "--help", help=help)
    out = capsys.readouterr().out
    assert "this is custom text" in out
