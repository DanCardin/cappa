from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from typing_extensions import Annotated

import cappa
from cappa import Subcommands
from tests.utils import backends, parse


@dataclass
class Example:
    subcommand: Subcommands[Union[A, None]] = None


@cappa.command(name="a")
@dataclass
class A:
    a: Annotated[str, cappa.Arg(value_name="<Str a>", short="-a")]


@backends
def test_value_name_uses_correct_value(backend):
    result = parse(Example, "a", "-a", "test", backend=backend)
    assert result == Example(subcommand=A(a="test"))
