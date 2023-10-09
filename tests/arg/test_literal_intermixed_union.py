from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Union

import cappa
import pytest

from tests.utils import backends, parse


@dataclass
class ArgTest:
    name: Union[int, Literal["one"]]


@backends
def test_valid_int(backend):
    test = parse(ArgTest, "5", backend=backend)
    assert test.name == 5


@backends
def test_valid_literal(backend):
    test = parse(ArgTest, "one", backend=backend)
    assert test.name == "one"


@backends
def test_invalid_string(backend):
    with pytest.raises(cappa.Exit) as e:
        parse(ArgTest, "thename", backend=backend)

    assert e.value.code == 2

    assert e.value.message == (
        "Invalid value for 'name' with value 'thename': "
        "Could not parse 'thename' given options: <int>, one"
    )
