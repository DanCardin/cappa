from __future__ import annotations

from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from cappa.invoke.types import InvokeResolutionError
from tests.utils import Backend, backends, invoke


def dependency():
    return 5


@dataclass
class Command:
    foo: int

    def __call__(self, dep: Annotated[int, cappa.Dep(dependency)]):
        return self.foo + dep


@backends
def test_invoke_top_level_command(backend: Backend):
    result = invoke(Command, "7", backend=backend)
    assert result == 7 + 5


@dataclass
class CommandWithUnannotatedCallParam:
    foo: int

    def __call__(self, x):  # pyright: ignore
        pass  # pragma: no cover


@backends
def test_unannotated_call_param_raises(backend: Backend):
    """Unannotated params in __call__ must not silently receive the class instance."""
    with pytest.raises(InvokeResolutionError):
        invoke(CommandWithUnannotatedCallParam, "7", backend=backend)
