from __future__ import annotations

import textwrap
from dataclasses import dataclass
from typing import Literal, Union

import pytest
from typing_extensions import Annotated

import cappa
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


@backends
def test_invalid_collection_of_literals(backend):
    @dataclass
    class Args:
        foo: Annotated[
            set[Literal["one", "two"]] | list[int] | None, cappa.Arg(short=True)
        ] = None

    with pytest.raises(cappa.Exit) as e:
        parse(Args, "-f", "three", backend=backend)

    assert e.value.code == 2

    err = textwrap.dedent(
        """\
        Invalid value for '-f': Possible variants
         - set[Literal['one', 'two']]: Invalid choice: 'three' (choose from literal values 'one', 'two')
         - list[int]: invalid literal for int() with base 10: 'three'
         - <no value>"""
    )
    assert str(e.value.message).lower() == err.lower()
