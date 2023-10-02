from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Union

import cappa
import pytest

from tests.utils import backends, parse


@dataclass
class ArgTest:
    name: Union[Literal["one"], Literal["two"], Literal["three"], Literal[4]]


@backends
def test_valid(backend):
    test = parse(ArgTest, "two", backend=backend)
    assert test.name == "two"


@backends
def test_valid_int(backend):
    test = parse(ArgTest, "4", backend=backend)
    assert test.name == 4


@backends
def test_invalid(backend):
    with pytest.raises(cappa.Exit) as e:
        parse(ArgTest, "thename", backend=backend)

    message = str(e.value.message).lower()
    assert (
        "invalid choice: 'thename' (choose from 'one', 'two', 'three', '4')" in message
    )
