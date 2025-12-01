from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends, parse


@dataclass
class Args:
    numbers: Annotated[
        list[int],
        cappa.Arg(
            long=True,
            default=[1, 2, 3],
            num_args=-1,
        ),
    ]


@backends
def test_num_args_unbounded_length_num_args(backend: Backend):
    result = parse(Args, backend=backend)
    assert result == Args([1, 2, 3])

    result = parse(Args, "--numbers", backend=backend)
    assert result == Args([])

    result = parse(Args, "--numbers", "2", backend=backend)
    assert result == Args([2])

    result = parse(Args, "--numbers", "2", "5", backend=backend)
    assert result == Args([2, 5])
