from __future__ import annotations

from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from cappa.parser import backend
from tests.utils import backends, parse


@backends
def test_invalid_choice_help(backend):
    @dataclass
    class Args:
        value: Annotated[str, cappa.Arg(long=True)]

    with pytest.raises(cappa.Exit) as e:
        parse(Args, "--value", "ok", "--meow", "wat", backend=backend)
    assert e.value.code == 2
    assert "unrecognized arguments: --meow" in str(e.value.message).lower()


def test_invalid_choice_help_possible_options():
    @dataclass
    class Args:
        value: Annotated[str, cappa.Arg(long=True)]

    with pytest.raises(cappa.Exit) as e:
        parse(Args, "--val", "on", backend=backend)
    assert e.value.code == 2
    assert "Unrecognized arguments: --val (Did you mean: --value)" in str(
        e.value.message
    )
