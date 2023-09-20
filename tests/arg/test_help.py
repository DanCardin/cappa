from __future__ import annotations

from dataclasses import dataclass

import cappa
import pytest
from typing_extensions import Annotated

from tests.utils import parse


def test_explicit_parse_function(capsys):
    @dataclass
    class ArgTest:
        numbers: Annotated[int, cappa.Arg(parse=int, help="example")]

    with pytest.raises(ValueError):
        parse(ArgTest, "--help")

    stdout = capsys.readouterr().out
    assert "numbers     example" in stdout
