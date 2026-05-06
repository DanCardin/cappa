from __future__ import annotations
from unittest.mock import patch

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from cappa import Env
from tests.utils import parse


@dataclass
class Foo:
    color: Annotated[str, cappa.Arg(long=True, default=Env("FOO"))]


@dataclass
class Args:
    attrs: cappa.Destructured[Foo]


def test_destructured():
    with patch("os.environ", new={"FOO": 'blue'}):
        test = parse(Args)

    assert test == Args(attrs=Foo('blue'))
