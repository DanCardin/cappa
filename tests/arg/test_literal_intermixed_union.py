from __future__ import annotations

import textwrap
from dataclasses import dataclass
from typing import Literal, Union

import pytest

import cappa
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

    err = textwrap.dedent(
        """\
        Invalid value for 'name': Possible variants
         - Literal['one']: Invalid choice: 'thename' (choose from literal values 'one')
         - int: invalid literal for int() with base 10: 'thename'"""
    )
    assert err in str(e.value.message)
