from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import cappa
import pytest
from typing_extensions import Annotated

from tests.utils import backends, parse


def split(value: str):
    a, b = value.split(",", 1)
    return int(a), int(b)


def parse_int(val):
    try:
        return int(val)
    except Exception:
        raise cappa.Exit("no go amego", code=2)


@backends
def test_explicit_parse_function(backend):
    @dataclass
    class ArgTest:
        numbers: Annotated[int, cappa.Arg(parse=int)]

    test = parse(ArgTest, "1", backend=backend)
    assert test.numbers == 1


@backends
def test_not_typeable_parse_function(backend):
    @dataclass
    class ArgTest:
        numbers: Annotated[Tuple[int, int], cappa.Arg(parse=split)]

    test = parse(ArgTest, "1,3", backend=backend)
    assert test.numbers == (1, 3)


@backends
def test_parse_failure(backend):
    """An explicit exit takes message precedence, and do not include extra cappa text."""

    @dataclass
    class ArgTest:
        numbers: Annotated[int, cappa.Arg(parse=parse_int)]

    with pytest.raises(cappa.Exit) as e:
        parse(ArgTest, "one", backend=backend)

    assert e.value.code == 2
    assert e.value.message == "no go amego"
