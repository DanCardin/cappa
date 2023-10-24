from __future__ import annotations

from dataclasses import dataclass
from typing import Union

import cappa
from cappa import Subcommands
from typing_extensions import Annotated

from tests.utils import backends, parse


@cappa.command(name="example")
@dataclass
class Example:
    subcommand: Subcommands[Union[A, None]] = None


@cappa.command(name="a")
@dataclass
class A:
    a: Annotated[str, cappa.Arg(value_name="<Str a>", short="-a", required=False)]


@backends
def test_value_name_uses_correct_value(backend):
    result = parse(Example, "a", "-a", "test", backend=backend)
    assert result == Example(subcommand=A(a="test"))
