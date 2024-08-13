from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Union

from typing_extensions import Annotated

import cappa
from cappa.parse import unpack_arguments
from tests.utils import backends, parse


@dataclass
class Single:
    value: str


@dataclass
class Double:
    one: str
    two: str


@dataclass
class Mapping:
    foo: str
    bar: str


@dataclass
class Args:
    single: Annotated[
        Union[Single, None], cappa.Arg(long=True, parse=unpack_arguments)
    ] = None
    double: Annotated[
        Union[Double, None],
        cappa.Arg(long=True, num_args=2, parse=unpack_arguments),
    ] = None
    mapping: Annotated[
        Union[Mapping, None],
        cappa.Arg(long=True, parse=[json.loads, unpack_arguments]),
    ] = None


@backends
def test_dataclass_annotation(backend):
    """Dataclass annotation will supply or splat arguments, depending on input shape."""
    result = parse(Args, backend=backend)
    assert result == Args()

    result = parse(Args, "--single=3", backend=backend)
    assert result.single == Single("3")
    assert result.double is None
    assert result.mapping is None

    result = parse(Args, "--double", "5", "10", backend=backend)
    assert result.single is None
    assert result.double == Double(one="5", two="10")
    assert result.mapping is None

    result = parse(Args, '--mapping={"foo": "8", "bar": "3"}', backend=backend)
    assert result.single is None
    assert result.double is None
    assert result.mapping == Mapping(foo="8", bar="3")
