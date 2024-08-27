from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@backends
def test_unrecognized_post_dash_arg(backend):
    @dataclass
    class Args:
        value: Annotated[str, cappa.Arg(long=True)]

    result = parse(Args, "--value=val", backend=backend)
    assert result == Args(value="val")
