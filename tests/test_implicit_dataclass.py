from __future__ import annotations

import cappa
from tests.utils import backends, parse


@cappa.command(name="sub")
class Example:
    bar: int
    name: str


@backends
def test_invoke_top_level_command(backend):
    result = parse(Example, "4", "foo", backend=backend)
    assert result == Example(bar=4, name="foo")


@backends
def test_no_args_command(backend):
    @cappa.command
    class Example:
        bar: int
        name: str

    result = parse(Example, "4", "foo", backend=backend)
    assert result == Example(bar=4, name="foo")
