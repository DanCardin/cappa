from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@backends
def test_invalid_choice_help(backend):
    @dataclass
    class Args:
        arg: str
        option: Annotated[str, cappa.Arg(long=True)]
        arg2: str
        option2: Annotated[str, cappa.Arg(long=True)]

    result = parse(
        Args, "arg", "--option=opt", "arg2", "--option2=opt2", backend=backend
    )
    assert result == Args(arg="arg", option="opt", arg2="arg2", option2="opt2")
