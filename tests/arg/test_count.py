from __future__ import annotations

from dataclasses import dataclass

import cappa
from typing_extensions import Annotated

from tests.utils import parse


def test_count_action():
    @dataclass
    class ArgTest:
        arg: Annotated[int, cappa.Arg(short=True, action=cappa.ArgAction.count)]

    result = parse(ArgTest, "-a")
    assert result.arg == 1

    result = parse(ArgTest, "-aaa")
    assert result.arg == 3


def test_count_option():
    @dataclass
    class ArgTest:
        arg: Annotated[int, cappa.Arg(short=True, count=True)]

    result = parse(ArgTest, "-a")
    assert result.arg == 1

    result = parse(ArgTest, "-aaa")
    assert result.arg == 3
