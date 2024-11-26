from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import parse


def test_unbounded_list_option():
    @dataclass
    class Args:
        unbounded: Annotated[list[list[int]], cappa.Arg(short=True)]

    result = parse(Args, "-u", "0")
    assert result == Args([[0]])

    result = parse(Args, "-u", "0", "1", "2", "3", "4", "5")
    assert result == Args([[0, 1, 2, 3, 4, 5]])


def test_unbounded_set_option():
    @dataclass
    class Args:
        unbounded: Annotated[set[tuple[int, int]], cappa.Arg(short=True)]

    result = parse(Args, "-u", "0", "1")
    assert result == Args({(0, 1)})


def test_unbounded_tuple_option():
    @dataclass
    class Args:
        unbounded: Annotated[tuple[list[int], ...], cappa.Arg(short=True)]

    result = parse(Args, "-u", "0")
    assert result == Args(([0],))

    result = parse(Args, "-u", "0", "1", "2", "3", "4", "5")
    assert result == Args(([0, 1, 2, 3, 4, 5],))
