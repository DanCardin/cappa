from __future__ import annotations

from dataclasses import dataclass

import cappa
import pytest
from typing_extensions import Annotated

from tests.utils import parse


def test_arg_name_disallowed():
    @dataclass
    class ArgTest:
        bad: Annotated[bool, cappa.Arg(name="oops")] = False

    with pytest.raises(
        ValueError, match="Arg 'name' cannot be set when using automatic inference."
    ):
        parse(ArgTest)
