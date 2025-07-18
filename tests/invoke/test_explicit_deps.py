from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends, invoke


def level_three():
    return {"level_three": True}


def level_two(level_three: Annotated[dict[str, Any], cappa.Dep(level_three)]):
    return {"level_two": {**level_three}}


def level_one(level_two: Annotated[dict[str, Any], cappa.Dep(level_two)]):
    return {"level_one": {**level_two}}


def command(levels: Annotated[dict[str, Any], cappa.Dep(level_one)]):
    return levels


@cappa.command(invoke=command)
@dataclass
class Command: ...


@backends
def test_invoke_top_level_command(backend: Backend):
    result = invoke(Command, backend=backend)
    assert result == {"level_one": {"level_two": {"level_three": True}}}
