from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Union

import pytest
from typing_extensions import Annotated, Doc

import cappa
from cappa.output import Exit
from tests.utils import backends, parse


@pytest.mark.help
@backends
def test_explicit_parse_function(backend, capsys):
    @dataclass
    class ArgTest:
        numbers: Annotated[int, cappa.Arg(parse=int, help="example")]

    with pytest.raises(Exit):
        parse(ArgTest, "--help", backend=backend)

    stdout = capsys.readouterr().out
    assert re.match(r".*NUMBERS\s+example.*", stdout, re.DOTALL)


@pytest.mark.help
@backends
def test_choices_in_help(backend, capsys):
    @dataclass
    class ArgTest:
        numbers: Annotated[
            Union[Literal[1], Literal[2]], cappa.Arg(parse=int, help="example")
        ]

    result = parse(ArgTest, "1", backend=backend)
    assert result == ArgTest(1)

    with pytest.raises(Exit):
        parse(ArgTest, "--help", backend=backend)

    stdout = capsys.readouterr().out
    assert "Valid options: 1, 2" in stdout


@pytest.mark.help
@backends
def test_pep_727_doc_annotated(backend, capsys):
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
        parse(ArgTest, "--help", backend=backend)

    stdout = capsys.readouterr().out
    assert "Use Doc if exists" in stdout
    assert "Doc beats docstring" in stdout

    assert "Arg wins" in stdout
    assert "Doc loses" not in stdout
