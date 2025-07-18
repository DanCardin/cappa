from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Union

import pytest
from type_lens.type_view import TypeView
from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends, parse


def split(value: str):
    a, b = value.split(",", 1)
    return int(a), int(b)


def parse_int(val: str) -> int:
    try:
        return int(val)
    except Exception:
        raise cappa.Exit("no go amego", code=2)


@backends
def test_explicit_parse_function(backend: Backend):
    @dataclass
    class ArgTest:
        numbers: Annotated[int, cappa.Arg(parse=int)]

    test = parse(ArgTest, "1", backend=backend)
    assert test.numbers == 1


@backends
def test_not_typeable_parse_function(backend: Backend):
    @dataclass
    class ArgTest:
        numbers: Annotated[tuple[int, int], cappa.Arg(parse=split)]

    test = parse(ArgTest, "1,3", backend=backend)
    assert test.numbers == (1, 3)


@backends
def test_parse_failure(backend: Backend):
    """Optional annotations should take precedence over explicit parse."""

    @dataclass
    class ArgTest:
        numbers: Annotated[int, cappa.Arg(parse=parse_int)]

    with pytest.raises(cappa.Exit) as e:
        parse(ArgTest, "one", backend=backend)

    assert e.value.code == 2
    assert e.value.message == "no go amego"


@backends
def test_parse_optional(backend: Backend):
    """Optionals are handled by the given/inferred parse method."""

    @dataclass
    class ArgTest:
        numbers: Annotated[Union[int, None], cappa.Arg(parse=float)] = None

    result = parse(ArgTest, backend=backend)
    assert result == ArgTest()

    with pytest.raises(cappa.Exit) as e:
        parse(ArgTest, "one", backend=backend)

    assert e.value.code == 2
    assert (
        e.value.message
        == "Invalid value for 'numbers': could not convert string to float: 'one'"
    )


def parse_test_parse_returns_none(value: str) -> bool | None:
    if int(value) % 2:
        return True
    return None


@backends
def test_parse_returns_none(backend: Backend):
    """Assert that a parser which returns None succeeds ."""

    @dataclass
    class ArgTest:
        numbers: Annotated[int | None, cappa.Arg(parse=parse_test_parse_returns_none)]

    result = parse(ArgTest, "1", backend=backend)
    assert result == ArgTest(True)

    result = parse(ArgTest, "2", backend=backend)
    assert result == ArgTest(None)


def parser_test_typed_parse(value: str):
    return float(value)


@backends
def test_typed_parse(backend: Backend):
    """A parse function with a typed argument."""

    @dataclass
    class ArgTest:
        num: Annotated[float, cappa.Arg(parse=parser_test_typed_parse)]

    result = parse(ArgTest, "4.1", backend=backend)
    assert result == ArgTest(num=4.1)


def parser_test_type_aware_parse(value: str, type_view: TypeView[Any]) -> str:
    return str(type_view)


@backends
def test_type_aware_parse(backend: Backend):
    """A parse function that receives type information."""

    @dataclass
    class ArgTest:
        num: Annotated[str, cappa.Arg(parse=parser_test_type_aware_parse)]

    result = parse(ArgTest, "4.1", backend=backend)
    assert result == ArgTest(num="TypeView(str)")


def parse_exit(_: Any) -> Any:
    raise cappa.Exit("asdf")


@backends
def test_parse_exit(backend: Backend):
    @dataclass
    class ArgTest:
        num: Annotated[str, cappa.Arg(parse=parse_exit)]

    with pytest.raises(cappa.Exit):
        parse(ArgTest, "4.1", backend=backend)


def min0(value: int) -> int:
    if not value > 0:
        raise ValueError(f"{value} > 0")
    return value


@backends
def test_default_parse(backend: Backend):
    @dataclass
    class ArgTest:
        num: Annotated[int, cappa.Arg(parse=[cappa.default_parse, min0])]

    result = parse(ArgTest, "4", backend=backend)
    assert result.num == 4

    with pytest.raises(cappa.Exit) as e:
        parse(ArgTest, "--", "-4", backend=backend)
    assert e.value.message == "Invalid value for 'num': -4 > 0"
