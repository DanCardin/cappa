from __future__ import annotations

from dataclasses import dataclass, field

from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@backends
def test_list_option(backend):
    @dataclass
    class ArgTest:
        variable_number: Annotated[set[str], cappa.Arg(short=True, long=True)] = field(
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
        backend=backend,
    )
    assert test.variable_number == {"one", "two"}


@backends
def test_list_positional(backend):
    @dataclass
    class ArgTest:
        variable_number: set[int] = field(default_factory=set)

    test = parse(
        ArgTest,
        "1",
        "2",
        "3",
        "2",
        "3",
        "1",
        backend=backend,
    )
    assert test.variable_number == {1, 2, 3}
