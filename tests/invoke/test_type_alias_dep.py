from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated, TypeAliasType

import cappa
from tests.utils import Backend, backends, invoke


def foo():
    return 45


Number = TypeAliasType("Number", Annotated[int, cappa.Dep(foo)])


@dataclass
class ArgTest:
    def __call__(self, value: Number) -> int:
        return value + 1


@backends
def test_scalar(backend: Backend):
    test = invoke(ArgTest, backend=backend)
    assert test == 46
