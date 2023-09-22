from __future__ import annotations

from dataclasses import dataclass, field
from typing import Set

import cappa
from typing_extensions import Annotated

from tests.utils import parse


def test_list_option():
    @dataclass
    class ArgTest:
        variable_number: Annotated[Set[str], cappa.Arg(short=True, long=True)] = field(
            default_factory=set
        )

    test = parse(
        ArgTest,
        "-v",
        "one",
        "--variable-number",
        "one",
        "--variable-number",
        "two",
        "-v",
        "two",
    )
    assert test.variable_number == {"one", "two"}


def test_list_positional():
    @dataclass
    class ArgTest:
        variable_number: Set[int] = field(default_factory=set)

    test = parse(
        ArgTest,
        "1",
        "2",
        "3",
        "2",
        "3",
        "1",
    )
    assert test.variable_number == {1, 2, 3}
