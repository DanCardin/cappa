from __future__ import annotations

from dataclasses import dataclass

from tests.utils import backends, parse


@backends
def test_positional_with_default_is_optional(backend):
    @dataclass
    class ArgTest:
        arg: int = 0

    result = parse(ArgTest, backend=backend)
    assert result.arg == 0


@backends
def test_multiple_positionals_fill_in_order(backend):
    @dataclass
    class ArgTest:
        arg: int = 0
        arg2: int = 0
        arg3: int = 0

    result = parse(ArgTest, "3", "5", backend=backend)
    assert result.arg == 3
    assert result.arg2 == 5
    assert result.arg3 == 0
