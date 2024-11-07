from __future__ import annotations

import re
from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@backends
def test_string_group(backend, capsys):
    @dataclass
    class Args:
        name: Annotated[str, cappa.Arg(group="Strings")]

    with pytest.raises(cappa.HelpExit) as e:
        parse(Args, "--help", backend=backend)

    assert e.value.code == 0

    out = capsys.readouterr().out
    assert re.match(r".*Strings:?\s*\n\s*NAME.*", out, re.DOTALL)


@backends
def test_tuple_group(backend, capsys):
    @dataclass
    class Args:
        name: Annotated[str, cappa.Arg(group=(1, "Strings"))]

    with pytest.raises(cappa.HelpExit) as e:
        parse(Args, "--help", backend=backend)

    assert e.value.code == 0

    out = capsys.readouterr().out
    assert re.match(r".*Strings:?\s*\n\s*NAME.*", out, re.DOTALL)
