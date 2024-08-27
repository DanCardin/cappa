from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import pytest
from rich.console import Console
from rich.text import Text
from typing_extensions import Annotated

import cappa
from tests.utils import parse


def test_line_wraps_correctly_with_terminal_escape_codes(capsys):
    @dataclass
    class Args:
        a: Annotated[str, cappa.Arg(short=True)]
        b: Annotated[str, cappa.Arg(short=True)]
        c: Annotated[str, cappa.Arg(short=True)]
        d: Annotated[str, cappa.Arg(short=True)]
        e: Annotated[str, cappa.Arg(short=True)]
        f: Annotated[str, cappa.Arg(short=True)]
        g: Annotated[str, cappa.Arg(short=True)]
        i: Annotated[str, cappa.Arg(short=True)]

    columns = 80
    env = {
        "FORCE_COLOR": "true",
        "COLUMNS": str(columns),
    }
    with patch("os.environ", new=env), pytest.raises(cappa.HelpExit) as e:
        output = cappa.Output(output_console=Console(force_terminal=True))
        parse(Args, "--help", output=output)

    assert e.value.code == 0

    out = capsys.readouterr().out
    plain, *_ = Text.from_ansi(out).plain.splitlines()

    expected = "Usage: args -a A -b B -c C -d D -e E -f F -g G -i I [-h] [--completion"
    assert len(expected) < columns
    assert plain == expected
