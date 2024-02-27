from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Union

import pytest

from tests.utils import backends, parse


@backends
def test_valid_tagged_unions(backend):
    @dataclass
    class ArgTest:
        name: Union[
            tuple[Literal["one"], str],
            tuple[Literal["two"], int],
            tuple[
                Literal["three"],
                float,
            ],
        ]

    test = parse(ArgTest, "one", "string", backend=backend)
    assert test.name == ("one", "string")

    test = parse(ArgTest, "two", "4", backend=backend)
    assert test.name == ("two", 4)

    test = parse(ArgTest, "three", "1.4", backend=backend)
    assert test.name == ("three", 1.4)


@backends
def test_disallowed_different_arity_variants(backend):
    @dataclass
    class ArgTest:
        name: Union[tuple[str, str], tuple[str, str, str]]

    with pytest.raises(ValueError) as e:
        parse(ArgTest, "one", "string", backend=backend)

    assert (
        str(e.value).lower().replace("typing.", "")
        == "on field 'name', mismatch of arity between union variants. `tuple[str, str]` produces `num_args=2`, `tuple[str, str, str]` produces `num_args=3`."
    )
