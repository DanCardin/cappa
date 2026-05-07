from __future__ import annotations

from dataclasses import dataclass
from typing import Union

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends, parse


@backends
def test_sequence_unioned_with_scalar(backend: Backend):
    """Inferred num_args: union arity mismatch caught in NumArgs.infer."""

    @dataclass
    class Args:
        foo: Union[list[str], str]

    with pytest.raises(ValueError) as e:
        parse(Args, "--help", backend=backend)

    exc = str(e.value).replace("typing.List", "list")
    assert exc == (
        "On field 'foo', mismatch of arity between union variants. "
        "`list[str]` produces `num_args=-1`, `<class 'str'>` produces `num_args=1`."
    )


@backends
def test_sequence_unioned_with_scalar_explicit_num_args(backend: Backend):
    """Explicit num_args bypasses NumArgs.infer union check; verify_type_compatibility catches it."""

    @dataclass
    class Args:
        foo: Annotated[Union[list[str], str], cappa.Arg(num_args=cappa.NumArgs(n=-1))]

    with pytest.raises(ValueError) as e:
        parse(Args, "--help", backend=backend)

    assert str(e.value) == (
        "On field 'foo', apparent mismatch of annotated type with `Arg` options. "
        'Unioning "sequence" types with non-sequence types is not currently supported, '
        "unless using `Arg(parse=...)` or `Arg(action=<callable>)`. "
        "See [documentation](https://cappa.readthedocs.io/en/latest/annotation.html) for more details."
    )


@backends
def test_sequence_with_scalar_action(backend: Backend):
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
def test_sequence_with_scalar_num_args(backend: Backend):
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
def test_scalar_with_sequence_action(backend: Backend):
    @dataclass
    class Args:
        foo: Annotated[str, cappa.Arg(action=cappa.ArgAction.append)]

    with pytest.raises(ValueError) as e:
        parse(Args, "--help", backend=backend)

    assert str(e.value) == (
        "On field 'foo', apparent mismatch of annotated type with `Arg` options. "
        "'str' type produces a scalar, whereas `num_args=1`/`action=ArgAction.append` do not. "
        "See [documentation](https://cappa.readthedocs.io/en/latest/annotation.html) for more details."
    )


@backends
def test_scalar_with_sequence_num_args(backend: Backend):
    @dataclass
    class Args:
        foo: Annotated[str, cappa.Arg(num_args=5)]

    with pytest.raises(ValueError) as e:
        parse(Args, "--help", backend=backend)

    assert str(e.value) == (
        "On field 'foo', apparent mismatch of annotated type with `Arg` options. "
        "'str' type produces a scalar, whereas `num_args=5`/`action=ArgAction.set` do not. "
        "See [documentation](https://cappa.readthedocs.io/en/latest/annotation.html) for more details."
    )


@backends
def test_num_args_optional_value_requires_optional_type(backend: Backend):
    """NumArgs(required=False, default=None) must pair with an Optional type."""

    @dataclass
    class Args:
        foo: Annotated[
            int, cappa.Arg(long=True, num_args=cappa.NumArgs(required=False))
        ] = 5

    with pytest.raises(ValueError) as e:
        parse(Args, "--help", backend=backend)

    assert str(e.value) == (
        "On field 'foo', `NumArgs(required=False, default=None)` requires the "
        "annotated type to include `None` (e.g. `int | None`), "
        "since the absent-value default of `None` is not assignable to the field type."
    )


@backends
def test_num_args_optional_value_non_none_default_does_not_require_optional_type(
    backend: Backend,
):
    """NumArgs(required=False, default=0) is valid with a non-optional type."""

    @dataclass
    class Args:
        foo: Annotated[
            int, cappa.Arg(long=True, num_args=cappa.NumArgs(required=False, default=0))
        ] = 5

    # Should not raise — default is a valid int, type need not include None.
    args = parse(Args, "--foo", backend=backend)
    assert args == Args(foo=0)
