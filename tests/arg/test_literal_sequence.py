from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Set, Tuple, Union

import pytest
from cappa import Arg
from typing_extensions import Annotated

from tests.utils import parse


@dataclass
class ArgTest:
    list: Annotated[
        List[Union[Literal["one"], Literal["two"], Literal["three"], Literal[4]]],
        Arg(short=True, default=[]),
    ]
    tuple: Annotated[
        Tuple[Union[Literal["one"], Literal["two"], Literal["three"], Literal[4]], ...],
        Arg(short=True, default=()),
    ]
    set: Annotated[
        Set[Union[Literal["one"], Literal["two"], Literal["three"], Literal[4]]],
        Arg(short=True, default=set()),
    ]


def test_list():
    test = parse(ArgTest, "-l", "one", "-l", "two")
    assert test.list == ["one", "two"]


def test_tuple():
    test = parse(ArgTest, "-t", "one", "-t", "two")
    assert test.tuple == ("one", "two")


def test_set():
    test = parse(ArgTest, "-s", "one", "-s", "two")
    assert test.set == {"one", "two"}


def test_invalid():
    with pytest.raises(
        ValueError,
        match=r"invalid choice: 'wat' \(choose from 'one', 'two', 'three', '4'\)",
    ):
        parse(ArgTest, "-l", "one", "-l", "wat")
