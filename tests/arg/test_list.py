from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import cappa
from typing_extensions import Annotated

from tests.utils import backends, parse


@backends
def test_list_option(backend):
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
        backend=backend,
    )
    assert test.variable_number == ["one", "two"]


@backends
def test_list_positional(backend):
    @dataclass
    class ArgTest:
        variable_number: List[str] = field(default_factory=list)

    test = parse(
        ArgTest,
        "one",
        "two",
        "three",
        backend=backend,
    )
    assert test.variable_number == ["one", "two", "three"]
