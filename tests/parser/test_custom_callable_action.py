from __future__ import annotations

from dataclasses import dataclass
from typing import Union

import pytest
from typing_extensions import Annotated

import cappa
from cappa.parser import Value
from tests.utils import backends, parse


################################
def exit():
    raise cappa.Exit("message")


@backends
def test_callable_action_fast_exits(backend):
    @dataclass
    class Args:
        value: Annotated[str, cappa.Arg(action=exit, short=True)]

    with pytest.raises(cappa.Exit) as e:
        parse(Args, "-v", "the", "rest", "is", "trash", backend=backend)
    assert e.value.message == "message"


################################
def truncate(value: Value[str]):
    return value.value[1:]


@backends
def test_uses_return_value(backend):
    @dataclass
    class Args:
        value: Annotated[str, cappa.Arg(action=truncate, short=True)]

    args = parse(Args, "-v", "okay", backend=backend)
    assert args.value == "kay"


@backends
def test_custom_arg(backend):
    @dataclass
    class Args:
        value: Annotated[str, cappa.Arg(action=truncate)]

    args = parse(Args, "okay", backend=backend)
    assert args.value == "kay"


################################
def command_name(command: cappa.Command):
    return command.real_name()


@dataclass
class SubBSub:
    value: Annotated[str, cappa.Arg(action=command_name, short=True)]


@dataclass
class SubA:
    value: Annotated[str, cappa.Arg(action=command_name, short=True)]


@dataclass
class SubB:
    cmd: cappa.Subcommands[SubBSub]


@backends
def test_subcommand_name(backend):
    @dataclass
    class Args:
        cmd: cappa.Subcommands[Union[SubA, SubB]]

    args = parse(Args, "sub-a", "-v", "one", backend=backend)
    assert args.cmd.value == "sub-a"

    args = parse(Args, "sub-b", "sub-b-sub", "-v", "one", backend=backend)
    assert args.cmd.cmd.value == "sub-b-sub"


################################
def custom_out(out: cappa.Output):
    out.output("woah")
    return 1


@backends
def test_custom_action_output_dep(backend, capsys):
    @dataclass
    class Args:
        value: Annotated[int, cappa.Arg(action=custom_out, short=True)]

    args = parse(Args, "-v", "one", backend=backend)
    assert args.value == 1

    out = capsys.readouterr().out
    assert out == "woah\n"
