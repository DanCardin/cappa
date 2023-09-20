from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import Tuple

import cappa

from tests.utils import parse


def test_positional_string():
    @dataclass
    class ArgTest:
        name: str

    test = parse(ArgTest, "thename")
    assert test.name == "thename"


def test_path():
    @dataclass
    class ArgTest:
        name: pathlib.PurePath

    test = parse(ArgTest, "./file.txt")
    assert test.name == pathlib.PurePath("./file.txt")


def test_bool():
    @dataclass
    class ArgTest:
        flag: bool

    test = parse(ArgTest, "--flag")
    assert test.flag is True


def test_tuple():
    @dataclass
    class ArgTest:
        exact_num_args: Tuple[str, int] = field(
            default=("a", 0), metadata={"cappa": cappa.Arg(long=True)}
        )

    test = parse(
        ArgTest,
        "--exact-num-args",
        "three",
        "4",
    )
    assert test.exact_num_args == ("three", 4)


def test_missing_value_defaults():
    @dataclass
    class ArgTest:
        exact_num_args: Tuple[str, int] = field(
            default=("a", 0), metadata={"cappa": cappa.Arg(long=True)}
        )

    test = parse(ArgTest)
    assert test.exact_num_args == ("a", 0)
