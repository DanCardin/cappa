from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import cappa

from tests.utils import invoke


def has_default(default: bool = True):
    return {"default": default}


def command(
    default: Annotated[dict, cappa.Dep(has_default)],
):
    return {"one": True, **default}


@cappa.command(invoke=command)
@dataclass
class Command:
    ...


def test_invoke_top_level_command():
    result = invoke(Command)
    assert result == {"one": True, "default": True}
