from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from typing_extensions import TypeAliasType

from tests.utils import Backend, backends, parse

Numbers = TypeAliasType("Numbers", Literal[1, 2, 3])


@backends
def test_manual_type_alias_type(backend: Backend):
    @dataclass
    class ArgTest:
        value: Numbers

    test = parse(ArgTest, "1", backend=backend)
    assert test.value == 1
