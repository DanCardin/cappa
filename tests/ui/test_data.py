from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pytest
from typing_extensions import Annotated

import cappa
from cappa.ui.data import ArgData, CommandData
from cappa.ui.parameter_controls import ValueNotSupplied


@dataclass
class FlatCmd:
    name: str
    flag: bool = False
    level: Annotated[Literal["a", "b", "c"], cappa.Arg(long=True)] = "a"
    count: Annotated[int, cappa.Arg(short=True)] = 0


@pytest.fixture()
def flat_args():
    cmd = cappa.collect(FlatCmd)
    return {a.field_name: a for a in cmd.value_arguments(exclude_subcommand=True)}


@pytest.fixture()
def flat_cmd():
    return cappa.collect(FlatCmd)


def test_positional_render(flat_args):
    ad = ArgData(flat_args["name"], ["hello"])
    assert list(ad.render()) == ["hello"]


def test_positional_unsupplied_renders_nothing(flat_args):
    ad = ArgData(flat_args["name"], [ValueNotSupplied()])
    assert list(ad.render()) == []


def test_option_render(flat_args):
    ad = ArgData(flat_args["count"], [42])
    assert list(ad.render()) == ["-c", 42]


def test_option_unsupplied_renders_nothing(flat_args):
    ad = ArgData(flat_args["count"], [ValueNotSupplied()])
    assert list(ad.render()) == []


def test_bool_flag_true_renders_name(flat_args):
    ad = ArgData(flat_args["flag"], [True])
    assert list(ad.render()) == ["--flag"]


def test_bool_flag_false_renders_nothing(flat_args):
    ad = ArgData(flat_args["flag"], [False])
    assert list(ad.render()) == []


def test_multiple_values(flat_args):
    ad = ArgData(flat_args["count"], [1, 2, 3])
    assert list(ad.render()) == ["-c", 1, "-c", 2, "-c", 3]


def test_command_data_to_cli_args_excludes_root(flat_cmd):
    arg_data = [
        ArgData(a, [ValueNotSupplied()])
        for a in flat_cmd.value_arguments(exclude_subcommand=True)
    ]
    cd = CommandData(command=flat_cmd, args_data=arg_data)
    assert cd.to_cli_args(include_root_command=False) == []


def test_command_data_to_cli_args_includes_values(flat_cmd):
    args = {a.field_name: a for a in flat_cmd.value_arguments(exclude_subcommand=True)}
    arg_data = [
        ArgData(args["name"], ["myservice"]),
        ArgData(args["flag"], [True]),
        ArgData(args["level"], [ValueNotSupplied()]),
        ArgData(args["count"], [ValueNotSupplied()]),
    ]
    cd = CommandData(command=flat_cmd, args_data=arg_data)
    assert cd.to_cli_args() == ["myservice", "--flag"]
