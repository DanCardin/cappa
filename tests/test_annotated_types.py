from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pytest
from annotated_types import (
    BaseMetadata,
    Ge,
    Gt,
    Interval,
    IsDigits,
    Le,
    Len,
    LowerCase,
    Lt,
    MaxLen,
    MinLen,
    MultipleOf,
    Predicate,
    Timezone,
    UpperCase,
)
from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends, parse


@dataclass
class Cmd:
    value: Annotated[int, cappa.Arg(), Gt(5)]


@backends
def test_gt_valid(backend: Backend):
    result = parse(Cmd, "10", backend=backend)
    assert result.value == 10


@backends
def test_gt_invalid(backend: Backend):
    with pytest.raises(cappa.Exit) as exc_info:
        parse(Cmd, "5", backend=backend)
    assert "Expected value > 5" in str(exc_info.value.message)


@dataclass
class GeCmd:
    value: Annotated[int, cappa.Arg(), Ge(5)]


@backends
def test_ge_valid(backend: Backend):
    result = parse(GeCmd, "5", backend=backend)
    assert result.value == 5


@backends
def test_ge_invalid(backend: Backend):
    with pytest.raises(cappa.Exit) as exc_info:
        parse(GeCmd, "4", backend=backend)
    assert "Expected value >= 5" in str(exc_info.value.message)


@dataclass
class LtCmd:
    value: Annotated[int, cappa.Arg(), Lt(10)]


@backends
def test_lt_valid(backend: Backend):
    result = parse(LtCmd, "9", backend=backend)
    assert result.value == 9


@backends
def test_lt_invalid(backend: Backend):
    with pytest.raises(cappa.Exit) as exc_info:
        parse(LtCmd, "10", backend=backend)
    assert "Expected value < 10" in str(exc_info.value.message)


@dataclass
class LeCmd:
    value: Annotated[int, cappa.Arg(), Le(10)]


@backends
def test_le_valid(backend: Backend):
    result = parse(LeCmd, "10", backend=backend)
    assert result.value == 10


@backends
def test_le_invalid(backend: Backend):
    with pytest.raises(cappa.Exit) as exc_info:
        parse(LeCmd, "11", backend=backend)
    assert "Expected value <= 10" in str(exc_info.value.message)


@dataclass
class IntervalCmd:
    value: Annotated[int, cappa.Arg(), Interval(ge=0, lt=100)]


@backends
def test_interval_valid(backend: Backend):
    result = parse(IntervalCmd, "50", backend=backend)
    assert result.value == 50


@backends
def test_interval_lower_invalid(backend: Backend):
    with pytest.raises(cappa.Exit):
        parse(IntervalCmd, "-1", backend=backend)


@backends
def test_interval_upper_invalid(backend: Backend):
    with pytest.raises(cappa.Exit):
        parse(IntervalCmd, "100", backend=backend)


@dataclass
class MultipleOfCmd:
    value: Annotated[int, cappa.Arg(), MultipleOf(3)]


@backends
def test_multiple_of_valid(backend: Backend):
    result = parse(MultipleOfCmd, "9", backend=backend)
    assert result.value == 9


@backends
def test_multiple_of_invalid(backend: Backend):
    with pytest.raises(cappa.Exit) as exc_info:
        parse(MultipleOfCmd, "10", backend=backend)
    assert "multiple of" in str(exc_info.value.message)


@dataclass
class MinLenCmd:
    value: Annotated[str, cappa.Arg(), MinLen(3)]


@backends
def test_min_len_valid(backend: Backend):
    result = parse(MinLenCmd, "abc", backend=backend)
    assert result.value == "abc"


@backends
def test_min_len_invalid(backend: Backend):
    with pytest.raises(cappa.Exit) as exc_info:
        parse(MinLenCmd, "ab", backend=backend)
    assert "Expected length >= 3" in str(exc_info.value.message)


@dataclass
class MaxLenCmd:
    value: Annotated[str, cappa.Arg(), MaxLen(3)]


@backends
def test_max_len_valid(backend: Backend):
    result = parse(MaxLenCmd, "abc", backend=backend)
    assert result.value == "abc"


@backends
def test_max_len_invalid(backend: Backend):
    with pytest.raises(cappa.Exit) as exc_info:
        parse(MaxLenCmd, "abcd", backend=backend)
    assert "Expected length <= 3" in str(exc_info.value.message)


@dataclass
class LenCmd:
    value: Annotated[str, cappa.Arg(), Len(2, 4)]


@backends
def test_len_valid(backend: Backend):
    result = parse(LenCmd, "abc", backend=backend)
    assert result.value == "abc"


@backends
def test_len_too_short(backend: Backend):
    with pytest.raises(cappa.Exit):
        parse(LenCmd, "a", backend=backend)


@backends
def test_len_too_long(backend: Backend):
    with pytest.raises(cappa.Exit):
        parse(LenCmd, "abcde", backend=backend)


@dataclass
class PredicateCmd:
    value: Annotated[str, cappa.Arg(), Predicate(str.isupper)]


@backends
def test_predicate_valid(backend: Backend):
    result = parse(PredicateCmd, "HELLO", backend=backend)
    assert result.value == "HELLO"


@backends
def test_predicate_invalid(backend: Backend):
    with pytest.raises(cappa.Exit) as exc_info:
        parse(PredicateCmd, "hello", backend=backend)
    assert "True" in str(exc_info.value.message)


@dataclass
class IsDigitsCmd:
    value: Annotated[str, cappa.Arg(), IsDigits]


@backends
def test_is_digits_valid(backend: Backend):
    result = parse(IsDigitsCmd, "123", backend=backend)
    assert result.value == "123"


@backends
def test_is_digits_invalid(backend: Backend):
    with pytest.raises(cappa.Exit):
        parse(IsDigitsCmd, "12a", backend=backend)


@dataclass
class UpperCaseCmd:
    value: Annotated[str, cappa.Arg(), UpperCase]


@backends
def test_upper_case_valid(backend: Backend):
    result = parse(UpperCaseCmd, "HELLO", backend=backend)
    assert result.value == "HELLO"


@backends
def test_upper_case_invalid(backend: Backend):
    with pytest.raises(cappa.Exit):
        parse(UpperCaseCmd, "hello", backend=backend)


@dataclass
class LowerCaseCmd:
    value: Annotated[str, cappa.Arg(), LowerCase]


@backends
def test_lower_case_valid(backend: Backend):
    result = parse(LowerCaseCmd, "hello", backend=backend)
    assert result.value == "hello"


@backends
def test_lower_case_invalid(backend: Backend):
    with pytest.raises(cappa.Exit):
        parse(LowerCaseCmd, "HELLO", backend=backend)


@dataclass
class TimezoneAwareCmd:
    value: Annotated[datetime, cappa.Arg(), Timezone(...)]  # pyright: ignore[reportUnknownArgumentType]


@backends
def test_timezone_aware_valid(backend: Backend):
    result = parse(TimezoneAwareCmd, "2024-01-01T12:00:00+00:00", backend=backend)
    assert result.value.tzinfo is not None


@backends
def test_timezone_aware_invalid(backend: Backend):
    with pytest.raises(cappa.Exit):
        parse(TimezoneAwareCmd, "2024-01-01T12:00:00", backend=backend)


@dataclass
class TimezoneNaiveCmd:
    value: Annotated[datetime, cappa.Arg(), Timezone(None)]


@backends
def test_timezone_naive_valid(backend: Backend):
    result = parse(TimezoneNaiveCmd, "2024-01-01T12:00:00", backend=backend)
    assert result.value.tzinfo is None


@backends
def test_timezone_naive_invalid(backend: Backend):
    with pytest.raises(cappa.Exit):
        parse(TimezoneNaiveCmd, "2024-01-01T12:00:00+00:00", backend=backend)


@dataclass
class TimezoneSpecificCmd:
    value: Annotated[datetime, cappa.Arg(), Timezone("UTC")]


@backends
def test_timezone_specific_naive_invalid(backend: Backend):
    with pytest.raises(cappa.Exit):
        parse(TimezoneSpecificCmd, "2024-01-01T12:00:00", backend=backend)


@dataclass
class TimezoneOnNonDatetimeCmd:
    value: Annotated[str, cappa.Arg(), Timezone(...)]  # pyright: ignore[reportUnknownArgumentType]


@backends
def test_timezone_on_non_datetime_passes(backend: Backend):
    result = parse(TimezoneOnNonDatetimeCmd, "hello", backend=backend)
    assert result.value == "hello"


@dataclass
class TimezoneSpecificAwareCmd:
    value: Annotated[datetime, cappa.Arg(), Timezone("UTC")]


@backends
def test_timezone_specific_aware_valid(backend: Backend):
    result = parse(
        TimezoneSpecificAwareCmd, "2024-01-01T12:00:00+00:00", backend=backend
    )
    assert result.value.tzinfo is not None


class UnknownMeta(BaseMetadata):
    pass


@dataclass
class UnknownMetaCmd:
    value: Annotated[int, cappa.Arg(), UnknownMeta()]


@backends
def test_unknown_metadata_ignored(backend: Backend):
    result = parse(UnknownMetaCmd, "42", backend=backend)
    assert result.value == 42
