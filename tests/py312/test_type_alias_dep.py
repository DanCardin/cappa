from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Annotated

import cappa
from tests.utils import Backend, backends, invoke


if sys.version_info >= (3, 12):
    def foo():
        return 45

    type Number = Annotated[int, cappa.Dep(foo)]  # pyright: ignore

    @dataclass
    class ArgTest:
        def __call__(self, value: Number) -> int:
            return value + 1

    @backends
    def test_scalar(backend: Backend):
        test = invoke(ArgTest, backend=backend)
        assert test == 46
