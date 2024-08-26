from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@backends
def test_(backend):
    @dataclass
    class Args:
        foo: Annotated[bool, cappa.Arg(long=True)] = False
        raw: Annotated[Union[list[str], None], cappa.Arg(num_args=-1)] = None

    test = parse(Args, "--foo", "--", "value", backend=backend)
    assert test.foo is True
    assert test.raw == ["value"]

    test = parse(Args, "--", "--foo", "value", backend=backend)
    assert test.foo is False
    assert test.raw == ["--foo", "value"]
