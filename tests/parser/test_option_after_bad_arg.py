from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

import cappa
from tests.utils import parse


@dataclass
class Args:
    arg: str


def test_option_after_bad_arg(capsys: Any):
    with pytest.raises(cappa.Exit):
        parse(Args, "arg1", "arg2", "--help")
    err = capsys.readouterr().err
    assert "Unrecognized arguments: arg2" in err
