from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import cappa
from typing_extensions import Annotated

from tests.utils import parse


def test_list_option():
    @dataclass
    class ArgTest:
        variable_number: Annotated[List[str], cappa.Arg(short=True, long=True)] = field(
            default_factory=list
        )

    test = parse(
        ArgTest,
        "-v",
        "one",
        "--variable-number",
        "two",
    )
    assert test.variable_number == ["one", "two"]


def test_list_positional():
    @dataclass
    class ArgTest:
        variable_number: List[str] = field(default_factory=list)

    test = parse(
        ArgTest,
        "one",
        "two",
        "three",
    )
    assert test.variable_number == ["one", "two", "three"]
