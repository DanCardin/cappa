from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends, parse


@dataclass
class Args:
    numbers: Annotated[str, cappa.Arg(parse=int, parse_inference=False)]


@backends
def test_disable_default_parser(backend: Backend):
    test = parse(Args, "1", backend=backend)
    assert test.numbers == 1
