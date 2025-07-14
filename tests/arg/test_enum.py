from __future__ import annotations

import enum
from dataclasses import dataclass

import pytest

import cappa
from tests.utils import Backend, backends, parse


class Options(enum.Enum):
    one = "one"
    two = "two"
    three = "three"


@dataclass
class ArgTest:
    options: Options


@backends
def test_valid(backend: Backend):
    test = parse(ArgTest, "two", backend=backend)
    assert test.options is Options.two


@backends
def test_invalid(backend: Backend):
    with pytest.raises(cappa.Exit) as e:
        parse(ArgTest, "thename", backend=backend)

    message = str(e.value.message).lower()
    assert "invalid choice: 'thename' (choose from 'one', 'two', 'three')" in message
