from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import parse_completion


def foo(f: str):
    return [cappa.Completion(f"{f}ooooo", "ok")]


def test_custom_completion():
    @dataclass
    class Args:
        value: Annotated[str, cappa.Arg(short=True, completion=foo)]

    result = parse_completion(Args, "-v", "f")
    assert result
    assert result == "fooooo:ok"
