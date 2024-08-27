from __future__ import annotations

import textwrap
from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import parse, strip_trailing_whitespace


def test_argument_name(capsys):
    @dataclass
    class Args:
        name: Annotated[str, cappa.Arg(value_name="string-name", help="more")]
        short: Annotated[str, cappa.Arg(short=True, value_name="optional-string")]

    with pytest.raises(cappa.HelpExit) as e:
        parse(Args, "--help")

    assert e.value.code == 0

    out = strip_trailing_whitespace(capsys.readouterr().out)

    assert out == textwrap.dedent(
        """\
        Usage: args -s OPTIONAL-STRING STRING-NAME [-h] [--completion COMPLETION]

          Options
            -s OPTIONAL-STRING

          Arguments
            STRING-NAME                more

          Help
            [-h, --help]               Show this message and exit.
            [--completion COMPLETION]  Use --completion generate to print shell-specific
                                       completion source. Valid options: generate,
                                       complete.
        """
    )
