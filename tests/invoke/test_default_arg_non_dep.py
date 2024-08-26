from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import backends, invoke


def has_default(default: bool = True):
    return {"default": default}


def command(
    default: Annotated[dict, cappa.Dep(has_default)],
):
    return {"one": True, **default}


@cappa.command(invoke=command)
@dataclass
class Command: ...


@backends
def test_invoke_top_level_command(backend):
    result = invoke(Command, backend=backend)
    assert result == {"one": True, "default": True}
