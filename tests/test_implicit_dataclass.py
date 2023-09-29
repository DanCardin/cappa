from __future__ import annotations

import cappa

from tests.utils import parse


@cappa.command(name="sub")
class Example:
    bar: int
    name: str


def test_invoke_top_level_command():
    result = parse(Example, "4", "foo")
    assert result == Example(bar=4, name="foo")
