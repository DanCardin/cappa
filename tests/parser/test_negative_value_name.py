from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends, parse


@backends
def test_negative_value_name_as_choice(backend: Backend):
    @dataclass
    class Args:
        level: Literal["-4", "-2", "0", "2", "4"]

    result = parse(Args, "-4", backend=backend)
    assert result == Args(level="-4")


@backends
def test_negative_value_name_with_option(backend: Backend):
    @dataclass
    class Args:
        verbose: Annotated[bool, cappa.Arg(short=True, default=False)]
        level: Literal["-4", "-2", "0", "2", "4"]

    result = parse(Args, "-v", "-4", backend=backend)
    assert result == Args(verbose=True, level="-4")


@backends
def test_negative_value_name_string_arg(backend: Backend):
    @dataclass
    class Args:
        option: Annotated[str, cappa.Arg(long=True)]
        level: Literal["-4", "-2", "0"]

    result = parse(Args, "--option", "foo", "-4", backend=backend)
    assert result == Args(option="foo", level="-4")
