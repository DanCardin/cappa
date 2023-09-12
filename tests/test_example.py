from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import Annotated

import cappa


def test_positional_string():
    @dataclass
    class ArgTest:
        name: str

    test = cappa.parse(ArgTest, argv=["thename"])
    assert test.name == "thename"


def test_path():
    @dataclass
    class ArgTest:
        name: pathlib.PurePath

    test = cappa.parse(ArgTest, argv=["./file.txt"])
    assert test.name == pathlib.PurePath("./file.txt")


def test_bool():
    @dataclass
    class ArgTest:
        flag: bool

    test = cappa.parse(ArgTest, argv=["--flag"])
    assert test.flag is True


def test_list():
    @dataclass
    class ArgTest:
        variable_number: Annotated[list[str], cappa.Arg(short=True, long=True)] = field(
            default_factory=list
        )

    test = cappa.parse(
        ArgTest,
        argv=[
            "-v",
            "one",
            "--variable-number",
            "two",
        ],
    )
    assert test.variable_number == ["one", "two"]


def test_tuple():
    @dataclass
    class ArgTest:
        exact_num_args: tuple[str, int] = field(
            default=("a", 0), metadata={"cappa": cappa.Arg(long=True)}
        )

    test = cappa.parse(
        ArgTest,
        argv=["--exact-num-args", "three", "4"],
    )
    assert test.exact_num_args == ("three", 4)


def test_missing_value_defaults():
    @dataclass
    class ArgTest:
        exact_num_args: tuple[str, int] = field(
            default=("a", 0), metadata={"cappa": cappa.Arg(long=True)}
        )

    test = cappa.parse(ArgTest, argv=[])
    assert test.exact_num_args == ("a", 0)
