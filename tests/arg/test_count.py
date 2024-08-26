from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@backends
def test_count_action(backend):
    @dataclass
    class ArgTest:
        arg: Annotated[int, cappa.Arg(short=True, action=cappa.ArgAction.count)]

    result = parse(ArgTest, "-a", backend=backend)
    assert result.arg == 1

    result = parse(ArgTest, "-aaa", backend=backend)
    assert result.arg == 3


@backends
def test_count_option(backend):
    @dataclass
    class ArgTest:
        arg: Annotated[int, cappa.Arg(short=True, count=True)]

    result = parse(ArgTest, "-a", backend=backend)
    assert result.arg == 1

    result = parse(ArgTest, "-aaa", backend=backend)
    assert result.arg == 3
