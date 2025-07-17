from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends, invoke

log = logging.getLogger("test")


def level_three():
    log.debug("three")
    return {"three": True}


def level_two(three: Annotated[dict[str, Any], cappa.Dep(level_three)]):
    log.debug("two")
    return {"two": {**three}}


def level_one(
    two: Annotated[dict[str, Any], cappa.Dep(level_two)],
    three: Annotated[dict[str, Any], cappa.Dep(level_three)],
):
    log.debug("one")
    return {"one": {**two, **three}}


def command(
    one: Annotated[dict[str, Any], cappa.Dep(level_one)],
    two: Annotated[dict[str, Any], cappa.Dep(level_two)],
    three: Annotated[dict[str, Any], cappa.Dep(level_three)],
):
    return {**one, **two, **three}


@cappa.command(invoke=command)
@dataclass
class Command: ...


@backends
def test_invoke_top_level_command(caplog: Any, backend: Backend):
    """Assert multiple paths to explicit dependencies are still fulfilled.

    * Ensure they are only called once overall, regardless of the number of downstream dependents.
    """
    caplog.set_level(logging.DEBUG)

    result = invoke(Command, backend=backend)

    assert result == {
        "one": {"two": {"three": True}, "three": True},
        "two": {"three": True},
        "three": True,
    }

    assert len(caplog.records) == 3
