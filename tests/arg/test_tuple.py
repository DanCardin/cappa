from __future__ import annotations

from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@dataclass
class ArgTest:
    numbers: tuple[int, str, float]


@backends
def test_valid(backend):
    test = parse(ArgTest, "1", "2", "3.4", backend=backend)
    assert test.numbers == (1, "2", 3.4)


@backends
def test_tuple_option(backend):
    @dataclass
    class Example:
        start_project: Annotated[
            tuple[int, float],
            cappa.Arg(short=True, default=(1, 9), required=False),
        ]

    test = parse(Example, backend=backend)
    assert test == Example(start_project=(1, 9))

    test = parse(Example, "-s", "2", "2.4", backend=backend)
    assert test == Example(start_project=(2, 2.4))

    # Missing values
    with pytest.raises(cappa.Exit) as e:
        parse(Example, "-s", "1", backend=backend)

    assert e.value.code == 2

    if backend:
        assert str(e.value.message).lower() == "argument -s: expected 2 arguments"
    else:
        assert (
            e.value.message == "Argument '-s' requires 2 values, found 1 ('1' so far)"
        )

    # Extra values
    with pytest.raises(cappa.Exit) as e:
        parse(Example, "-s", "1", "2", "3", backend=backend)
    assert e.value.code == 2
    assert str(e.value.message).lower() == "unrecognized arguments: 3"


@backends
def test_optional_tuple_option(backend):
    @dataclass
    class Example:
        start_project: Annotated[
            tuple[int, float] | None,
            cappa.Arg(short=True, required=False),
        ] = None

    test = parse(Example, backend=backend)
    assert test == Example(start_project=None)

    test = parse(Example, "-s", "2", "2.4", backend=backend)
    assert test == Example(start_project=(2, 2.4))

    # Missing values
    with pytest.raises(cappa.Exit) as e:
        parse(Example, "-s", "1", backend=backend)

    assert e.value.code == 2

    if backend:
        assert str(e.value.message).lower() == "argument -s: expected 2 arguments"
    else:
        assert (
            e.value.message == "Argument '-s' requires 2 values, found 1 ('1' so far)"
        )

    # Extra values
    with pytest.raises(cappa.Exit) as e:
        parse(Example, "-s", "1", "2", "3", backend=backend)
    assert e.value.code == 2
    assert str(e.value.message).lower() == "unrecognized arguments: 3"
