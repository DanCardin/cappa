from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Union

import cappa
import pytest
from cappa.output import Exit
from typing_extensions import Annotated, Doc  # type: ignore

from tests.utils import parse


@pytest.mark.help
def test_explicit_parse_function(capsys):
    @dataclass
    class ArgTest:
        numbers: Annotated[int, cappa.Arg(parse=int, help="example")]

    with pytest.raises(Exit):
        parse(ArgTest, "--help")

    stdout = capsys.readouterr().out
    assert "numbers     example" in stdout


@pytest.mark.help
def test_choices_in_help(capsys):
    @dataclass
    class ArgTest:
        numbers: Annotated[
            Union[Literal[1], Literal[2]], cappa.Arg(parse=int, help="example")
        ]

    result = parse(ArgTest, "1")
    assert result == ArgTest(1)

    with pytest.raises(Exit):
        parse(ArgTest, "--help")

    stdout = capsys.readouterr().out
    assert "Valid options: 1, 2" in stdout


@pytest.mark.help
def test_pep_727_doc_annotated(capsys):
    @dataclass
    class ArgTest:
        """Test.

        Arguments:
            doc_beats_docstring: loses.
        """

        only_doc: Annotated[int, cappa.Arg(parse=int), Doc("Use Doc if exists")]
        doc_beats_docstring: Annotated[
            int, cappa.Arg(parse=int), Doc("Doc beats docstring")
        ]
        prefer_arg: Annotated[
            int, cappa.Arg(parse=int, help="Arg wins"), Doc("Doc loses")
        ]

    with pytest.raises(Exit):
        parse(ArgTest, "--help")

    stdout = capsys.readouterr().out
    assert "Use Doc if exists" in stdout
    assert "Doc beats docstring" in stdout

    assert "Arg wins" in stdout
    assert "Doc loses" not in stdout
