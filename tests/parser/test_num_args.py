from __future__ import annotations

from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


def action():
    raise cappa.Exit()


@backends
def test_single_opt(backend):
    @dataclass
    class Args:
        kill_switch: Annotated[
            bool, cappa.Arg(long="--kill", action=action, num_args=0)
        ]
        required: str

    with pytest.raises(cappa.Exit) as e:
        parse(Args, "--kill", backend=backend)

    assert e.value.message is None
    assert e.value.code == 0


@backends
def test_num_args_list(backend):
    @dataclass
    class Args:
        foo: Annotated[
            list[str],
            cappa.Arg(
                short=True,
                default=["", ""],
                required=False,
                num_args=2,
            ),
        ]

    args = parse(Args, backend=backend)
    assert args == Args(["", ""])

    args = parse(Args, "-f", "2", "4", backend=backend)
    assert args == Args(["2", "4"])

    with pytest.raises(cappa.Exit) as e:
        parse(Args, "-f", backend=backend)

    assert e.value.code == 2

    if backend:
        assert str(e.value.message).lower() == "argument -f: expected 2 arguments"
    else:
        assert e.value.message == "Argument '-f' requires 2 values, found 0"
