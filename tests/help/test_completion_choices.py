from __future__ import annotations

import re
from dataclasses import dataclass

import pytest

import cappa
from tests.utils import parse


def test_string_group(capsys):
    @dataclass
    class Args: ...

    with pytest.raises(cappa.HelpExit) as e:
        parse(Args, "--help", backend=cappa.backend)

    assert e.value.code == 0

    out = capsys.readouterr().out

    options = re.findall(r"Valid\s+options:\s+generate,\s+complete", out, re.MULTILINE)
    assert len(options) == 1
