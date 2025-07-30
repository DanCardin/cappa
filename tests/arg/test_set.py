from __future__ import annotations

from dataclasses import dataclass, field

from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends, parse


@backends
def test_list_option(backend: Backend):
    @dataclass
    class ArgTest:
        variable_number: Annotated[set[str], cappa.Arg(short=True, long=True)] = field(
            default_factory=lambda: set()
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
def test_list_positional(backend: Backend):
    @dataclass
    class ArgTest:
        variable_number: set[int] = field(default_factory=lambda: set())

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
