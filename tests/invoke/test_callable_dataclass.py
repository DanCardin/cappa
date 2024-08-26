from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import backends, invoke


def dependency():
    return 5


@dataclass
class Command:
    foo: int

    def __call__(self, dep: Annotated[int, cappa.Dep(dependency)]):
        return self.foo + dep


@backends
def test_invoke_top_level_command(backend):
    result = invoke(Command, "7", backend=backend)
    assert result == 7 + 5
