from __future__ import annotations

from dataclasses import dataclass

import cappa
import pytest
from typing_extensions import Annotated

from tests.utils import parse


def test_manually_specified_choices():
    @dataclass
    class ArgTest:
        choice: Annotated[str, cappa.Arg(choices=["a", "1"])]

    result = parse(ArgTest, "a")
    assert result.choice == "a"

    result = parse(ArgTest, "1")
    assert result.choice == "1"

    with pytest.raises(
        ValueError,
        match=r"argument choice: invalid choice: 'two' \(choose from 'a', '1'\)",
    ):
        parse(ArgTest, "two")
