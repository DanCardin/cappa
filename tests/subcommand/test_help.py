from __future__ import annotations

from dataclasses import dataclass

import cappa
import pytest
from cappa.output import Exit
from typing_extensions import Annotated, Doc  # type: ignore

from tests.utils import parse


@dataclass
class Cmd:
    foo: int


@pytest.mark.help
def test_pep_727_doc_annotated_arg_wins(capsys):
    @dataclass
    class ArgTest:
        subcommand: Annotated[Cmd, cappa.Subcommand(help="Arg wins"), Doc("Doc loses")]

    with pytest.raises(Exit):
        parse(ArgTest, "--help")

    stdout = capsys.readouterr().out
    assert "Arg wins" in stdout
    assert "Doc loses" not in stdout


@pytest.mark.help
def test_pep_727_doc_annotated_doc_beats_docstring(capsys):
    @dataclass
    class ArgTest:
        """Test.

        Arguments:
            subcommand: docstring loses
        """

        subcommand: Annotated[Cmd, cappa.Subcommand, Doc("Doc wins")]

    with pytest.raises(Exit):
        parse(ArgTest, "--help")

    stdout = capsys.readouterr().out
    assert "Doc wins" in stdout
    assert "docstring loses" not in stdout
