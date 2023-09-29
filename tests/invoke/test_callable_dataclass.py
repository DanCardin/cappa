from __future__ import annotations

from dataclasses import dataclass

import cappa
from typing_extensions import Annotated

from tests.utils import invoke


def dependency():
    return 5


@dataclass
class Command:
    foo: int

    def __call__(self, dep: Annotated[int, cappa.Dep(dependency)]):
        return self.foo + dep


def test_invoke_top_level_command():
    result = invoke(Command, "7")
    assert result == 7 + 5
