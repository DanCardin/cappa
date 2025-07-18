from __future__ import annotations

from dataclasses import dataclass
from typing import Union

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends, parse


@dataclass
class Command:
    a: Annotated[str, cappa.Arg(short=True)]
    b: Annotated[str, cappa.Arg(short=True, required=True)] = "asdf"


@backends
def test_required_implicit(backend: Backend):
    with pytest.raises(cappa.Exit) as e:
        parse(Command, "-b", "b", backend=backend)

    assert e.value.code == 2
    assert "are required: -a" in str(e.value.message)

    result = parse(Command, "-a", "a", "-b", "b", backend=backend)
    assert result == Command(a="a", b="b")


@backends
def test_required_explicit(backend: Backend):
    with pytest.raises(cappa.Exit) as e:
        parse(Command, "-a", "a", backend=backend)

    assert e.value.code == 2
    assert "are required: -b" in str(e.value.message)

    result = parse(Command, "-a", "a", "-b", "b")
    assert result == Command(a="a", b="b")


@backends
def test_required_lists_all(backend: Backend):
    with pytest.raises(cappa.Exit) as e:
        parse(Command, backend=backend)

    assert e.value.code == 2
    assert "are required: -a, -b" in str(e.value.message)


@backends
def test_required_explicit_false(backend: Backend):
    @dataclass
    class Example:
        a: Annotated[str, cappa.Arg(short="-a", required=False)]
        c: Annotated[str, cappa.Arg(short="-c", required=False)]

    with pytest.raises(ValueError) as e:
        parse(Example, "-a", "a", backend=backend)

    assert (
        "When specifying `required=False`, a default value must be supplied able to be "
        "supplied through type inference, `Arg(default=...)`, or through class-level default"
    ) == str(e.value)


@backends
def test_required_explicit_false_union_none_no_explicit_default(backend: Backend):
    @dataclass
    class Example:
        c: Annotated[Union[str, None], cappa.Arg(short="-c", required=False)]

    result = parse(Example, backend=backend)
    assert result == Example(c=None)

    result = parse(Example, "-c", "c", backend=backend)
    assert result == Example(c="c")


@backends
def test_required_unbounded_list(backend: Backend):
    @dataclass
    class Example:
        c: Annotated[list[str], cappa.Arg(required=True)]

    with pytest.raises(cappa.Exit) as e:
        parse(Example, backend=backend)
    assert "require" in str(e.value.message)

    result = parse(Example, "c", backend=backend)
    assert result == Example(["c"])


@backends
def test_required_option(backend: Backend):
    @dataclass
    class Example:
        c: Annotated[list[str], cappa.Arg(short=True, required=True)]

    with pytest.raises(cappa.Exit) as e:
        parse(Example, backend=backend)
    assert "the following arguments are required: -c" == str(e.value.message).lower()

    result = parse(Example, "-c", "c", backend=backend)
    assert result == Example(["c"])
