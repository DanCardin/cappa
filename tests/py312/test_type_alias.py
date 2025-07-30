from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Annotated, Literal

import cappa
from tests.utils import Backend, backends, parse


if sys.version_info >= (3, 12):
    type Numbers = Literal[1, 2, 3]  # pyright: ignore

    @backends
    def test_scalar(backend: Backend):
        @dataclass
        class ArgTest:
            value: Numbers

        test = parse(ArgTest, "1", backend=backend)
        assert test.value == 1

    @backends
    def test_list_numbers(backend: Backend):
        @dataclass
        class ArgTest:
            value: list[Numbers]

        test = parse(ArgTest, "1", backend=backend)
        assert test.value == [1]

    @backends
    def test_annotated(backend: Backend):
        @dataclass
        class ArgTest:
            value: Annotated[Numbers, cappa.Arg()]

        test = parse(ArgTest, "1", backend=backend)
        assert test.value == 1
