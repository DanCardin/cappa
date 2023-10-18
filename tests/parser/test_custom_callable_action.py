from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union

import cappa
from typing_extensions import Annotated

from tests.utils import backends, parse


@backends
def test_callable_action_fast_exit(backend):
    @dataclass
    class Args:
        foo: str
        raw: Annotated[Union[List[str], None], cappa.Arg(num_args=-1)] = None

    test = parse(Args, "foovalue", "--", "--raw", "value", backend=backend)
    assert test.foo == "foovalue"
    assert test.raw == ["--raw", "value"]
