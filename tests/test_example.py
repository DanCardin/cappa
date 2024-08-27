from __future__ import annotations

import pathlib
from dataclasses import dataclass, field

import cappa
from tests.utils import backends, parse


@backends
def test_positional_string(backend):
    @dataclass
    class ArgTest:
        name: str

    test = parse(ArgTest, "thename", backend=backend)
    assert test.name == "thename"


@backends
def test_path(backend):
    @dataclass
    class ArgTest:
        name: pathlib.PurePath

    test = parse(ArgTest, "./file.txt", backend=backend)
    assert test.name == pathlib.PurePath("./file.txt")


@backends
def test_bool(backend):
    @dataclass
    class ArgTest:
        flag: bool

    test = parse(ArgTest, "--flag", backend=backend)
    assert test.flag is True


@backends
def test_tuple(backend):
    @dataclass
    class ArgTest:
        exact_num_args: tuple[str, int] = field(
            default=("a", 0), metadata={"cappa": cappa.Arg(long=True)}
        )

    test = parse(
        ArgTest,
        "--exact-num-args",
        "three",
        "4",
        backend=backend,
    )
    assert test.exact_num_args == ("three", 4)


@backends
def test_missing_value_defaults(backend):
    @dataclass
    class ArgTest:
        exact_num_args: tuple[str, int] = field(
            default=("a", 0), metadata={"cappa": cappa.Arg(long=True)}
        )

    test = parse(ArgTest, backend=backend)
    assert test.exact_num_args == ("a", 0)
