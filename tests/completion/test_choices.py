from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from typing_extensions import Annotated, Literal

import cappa
from tests.utils import parse_completion


def test_choices_without_help():
    @dataclass
    class Args:
        value: Union[Literal["one"], Literal["two"], Literal["three"]]

    result = parse_completion(Args, "")
    assert result
    assert result == "one:\ntwo:\nthree:"


def test_choices_with_help():
    @dataclass
    class Args:
        value: Annotated[
            Union[Literal["one"], Literal["two"], Literal["three"]],
            cappa.Arg(help="helpful"),
        ]

    result = parse_completion(Args, "")
    assert result
    assert result == "one:helpful\ntwo:helpful\nthree:helpful"


def test_half_string():
    @dataclass
    class Args:
        value: Union[Literal["one"], Literal["two"], Literal["three"]]

    result = parse_completion(Args, "'on")
    assert result
    assert result == "one:"
