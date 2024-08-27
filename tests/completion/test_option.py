from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import parse_completion


def test_long_option_name():
    @dataclass
    class Args:
        default: bool = False

    result = parse_completion(Args, "--d")
    assert result == "--default:"


def test_long_option_name_with_help():
    @dataclass
    class Args:
        default: Annotated[bool, cappa.Arg(help="Enables default")] = False

    result = parse_completion(Args, "--d")
    assert result == "--default:Enables default"


def test_mulitple_matches():
    @dataclass
    class Args:
        apple: Annotated[str, cappa.Arg(short=True, help="apple")]
        banana: Annotated[str, cappa.Arg(short=True, help="banana")]

    result = parse_completion(Args, "-")
    assert result
    assert "-a:apple\n-b:banana" in result


def test_short_name():
    @dataclass
    class Args:
        apple: Annotated[str, cappa.Arg(short=True)]

    result = parse_completion(Args, "-a")
    assert result is None
