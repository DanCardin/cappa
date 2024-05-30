from __future__ import annotations

from dataclasses import dataclass
from typing import Union

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@backends
def test_sequence_unioned_with_scalar(backend):
    @dataclass
    class Args:
        foo: Union[list[str], str]

    with pytest.raises(ValueError) as e:
        parse(Args, "--help", backend=backend)

    assert str(e.value) == (
        "On field 'foo', apparent mismatch of annotated type with `Arg` options. "
        'Unioning "sequence" types with non-sequence types is not currently supported, '
        "unless using `Arg(parse=...)` or `Arg(action=<callable>)`. "
        "See [documentation](https://cappa.readthedocs.io/en/latest/annotation.html) for more details."
    )


@backends
def test_sequence_with_scalar_action(backend):
    @dataclass
    class Args:
        foo: Annotated[list[str], cappa.Arg(action=cappa.ArgAction.set, num_args=1)]

    with pytest.raises(ValueError) as e:
        parse(Args, "--help", backend=backend)

    result = str(e.value).replace("List", "list")
    assert result == (
        "On field 'foo', apparent mismatch of annotated type with `Arg` options. "
        "'list[str]' type produces a sequence, whereas `num_args=1`/`action=ArgAction.set` do not. "
        "See [documentation](https://cappa.readthedocs.io/en/latest/annotation.html) for more details."
    )


@backends
def test_sequence_with_scalar_num_args(backend):
    @dataclass
    class Args:
        foo: Annotated[list[str], cappa.Arg(num_args=1, short=True)]

    args = parse(Args, "-f", "a", "-f", "b", backend=backend)
    assert args == Args(["a", "b"])

    @dataclass
    class ArgsBad:
        foo: Annotated[
            list[str], cappa.Arg(num_args=1, short=True, action=cappa.ArgAction.set)
        ]

    with pytest.raises(ValueError) as e:
        parse(ArgsBad, "--help", backend=backend)

    result = str(e.value).replace("List", "list")
    assert result == (
        "On field 'foo', apparent mismatch of annotated type with `Arg` options. "
        "'list[str]' type produces a sequence, whereas `num_args=1`/`action=ArgAction.set` do not. "
        "See [documentation](https://cappa.readthedocs.io/en/latest/annotation.html) for more details."
    )


@backends
def test_scalar_with_sequence_action(backend):
    @dataclass
    class Args:
        foo: Annotated[str, cappa.Arg(action=cappa.ArgAction.append)]

    with pytest.raises(ValueError) as e:
        parse(Args, "--help", backend=backend)

    assert str(e.value) == (
        "On field 'foo', apparent mismatch of annotated type with `Arg` options. "
        "'str' type produces a scalar, whereas `num_args=None`/`action=ArgAction.append` do not. "
        "See [documentation](https://cappa.readthedocs.io/en/latest/annotation.html) for more details."
    )


@backends
def test_scalar_with_sequence_num_args(backend):
    @dataclass
    class Args:
        foo: Annotated[str, cappa.Arg(num_args=5)]

    with pytest.raises(ValueError) as e:
        parse(Args, "--help", backend=backend)

    assert str(e.value) == (
        "On field 'foo', apparent mismatch of annotated type with `Arg` options. "
        "'str' type produces a scalar, whereas `num_args=5`/`action=None` do not. "
        "See [documentation](https://cappa.readthedocs.io/en/latest/annotation.html) for more details."
    )
