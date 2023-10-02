from __future__ import annotations

from dataclasses import dataclass

from tests.utils import parse_completion


def test_arg():
    @dataclass
    class Args:
        value: str

    result = parse_completion(Args, "")
    assert not result


def test_arg_partial():
    @dataclass
    class Args:
        value: str

    result = parse_completion(Args, "m")
    assert result
    assert result == "file"
