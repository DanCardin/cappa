from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@backends
def test_collect_post_dash_args(backend):
    @dataclass
    class Args:
        foo: str
        raw: Annotated[Union[list[str], None], cappa.Arg(num_args=-1)] = None

    test = parse(Args, "foovalue", "--", "--raw", "value", backend=backend)
    assert test.foo == "foovalue"
    assert test.raw == ["--raw", "value"]
