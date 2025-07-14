from __future__ import annotations

from dataclasses import dataclass

import pytest
from typing_extensions import Annotated, Literal

import cappa
from tests.utils import Backend, backends, parse


@dataclass
class ArgTest:
    list: Annotated[
        list[Literal["one", "two", "three", 4]],
        cappa.Arg(short=True, default=[]),
    ]
    tuple: Annotated[
        tuple[Literal["one", "two", "three", 4], ...],
        cappa.Arg(short=True, default=()),
    ]
    set: Annotated[
        set[Literal["one", "two", "three", 4]],
        cappa.Arg(short=True, default=set()),  # pyright: ignore
    ]


@backends
def test_list(backend: Backend):
    test = parse(ArgTest, "-l", "one", "-l", "two", backend=backend)
    assert test.list == ["one", "two"]


@backends
def test_tuple(backend: Backend):
    test = parse(ArgTest, "-t", "one", "-t", "two", backend=backend)
    assert test.tuple == ("one", "two")


@backends
def test_set(backend: Backend):
    test = parse(ArgTest, "-s", "one", "-s", "two", backend=backend)
    assert test.set == {"one", "two"}


@backends
def test_invalid(backend: Backend):
    with pytest.raises(cappa.Exit) as e:
        parse(ArgTest, "-l", "one", "-l", "wat", backend=backend)

    message = str(e.value.message).lower()
    assert "invalid choice: 'wat' (choose from 'one', 'two', 'three', 4)" in message
