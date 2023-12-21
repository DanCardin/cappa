from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Union

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


@backends
def test_optional_list(backend):
    @dataclass
    class ArgTest:
        value: Annotated[
            Union[List[str], None], cappa.Arg(short=True, long=True)
        ] = None

    test = parse(
        ArgTest,
        "--value=one",
        "--value=two",
        backend=backend,
    )
    assert test.value == ["one", "two"]

    test = parse(ArgTest, backend=backend)
    assert test.value is None
