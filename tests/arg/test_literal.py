from __future__ import annotations

import textwrap
from dataclasses import dataclass
from typing import Literal, Union

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@backends
def test_valid(backend):
    @dataclass
    class ArgTest:
        name: Literal["one", "two"]

    test = parse(ArgTest, "two", backend=backend)
    assert test.name == "two"


@backends
def test_valid_int(backend):
    @dataclass
    class ArgTest:
        name: Literal["one", 4]

    test = parse(ArgTest, "4", backend=backend)
    assert test.name == 4


@backends
def test_invalid(backend):
    @dataclass
    class ArgTest:
        name: Literal["one", "two", "three", 4]

    with pytest.raises(cappa.Exit) as e:
        parse(ArgTest, "thename", backend=backend)

    message = str(e.value.message).lower()
    assert "invalid choice: 'thename' (choose from 'one', 'two', 'three', 4)" in message


@backends
def test_unioned_literals(backend):
    @dataclass
    class ArgTest:
        name: Union[Literal["one"], Literal["two"], Literal["three"], Literal[4]]

    with pytest.raises(cappa.Exit) as e:
        parse(ArgTest, "thename", backend=backend)

    message = str(e.value.message).lower()
    assert (
        "invalid value for 'name': possible variants\n - literal['one']: invalid choice: 'thename' (choose from 'one')\n - literal['two']: invalid choice: 'thename' (choose from 'two')\n - literal['three']: invalid choice: 'thename' (choose from 'three')\n - literal[4]: invalid choice: 'thename' (choose from 4)"
        == message
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
         - set[Literal['one', 'two']]: Invalid choice: 'three' (choose from 'one', 'two')
         - list[int]: invalid literal for int() with base 10: 'three'
         - <no value>"""
    )
    assert str(e.value.message).lower() == err.lower()


@backends
def test_literal_parse(backend):
    @dataclass
    class LiteralParse:
        log_level: Annotated[
            Literal["TRACE", "DEBUG", "INFO"],
            cappa.Arg(short="-L", long=True, parse=str.upper),
        ] = "INFO"

    result = parse(LiteralParse, "--log-level=debug", backend=backend)
    assert result == LiteralParse(log_level="DEBUG")
