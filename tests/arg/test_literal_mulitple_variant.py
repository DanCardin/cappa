from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pytest

import cappa
from tests.utils import backends, parse


@dataclass
class ArgTest:
    name: Literal["one", "two", "three", 4]


@backends
def test_literal(backend):
    test = parse(ArgTest, "two", backend=backend)
    assert test.name == "two"

    test = parse(ArgTest, "4", backend=backend)
    assert test.name == 4

    with pytest.raises(cappa.Exit) as e:
        parse(ArgTest, "thename", backend=backend)

    message = str(e.value.message).lower()
    assert (
        "invalid choice: 'thename' (choose from 'one', 'two', 'three', '4')" in message
    )
