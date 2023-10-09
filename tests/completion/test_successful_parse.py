from __future__ import annotations

from dataclasses import dataclass

from tests.utils import parse_completion


def test_long_option_name():
    @dataclass
    class Args:
        default: bool = False

    result = parse_completion(Args, "--default")
    assert result is None
