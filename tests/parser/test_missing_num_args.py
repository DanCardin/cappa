from __future__ import annotations

from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from cappa import argparse
from tests.utils import backends, parse


@backends
def test_invalid_choice_help(backend):
    @dataclass
    class Args:
        arg: tuple[str, str]
        option: Annotated[str, cappa.Arg(long=True)]

    with pytest.raises(cappa.Exit) as e:
        parse(Args, "arg", "--option=opt", backend=backend)
    assert e.value.code == 2

    message = str(e.value.message)
    if backend == argparse.backend:
        assert "the following arguments are required: arg" in message.lower()
    else:
        assert message == "Argument 'arg arg' requires 2 values, found 1 ('arg' so far)"
