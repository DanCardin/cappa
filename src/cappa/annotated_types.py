"""Optional integration with the annotated-types library.

When `annotated-types` is installed, constraints like `Gt(5)` found in
`Annotated[int, Gt(5)]` are automatically applied as post-parse validators.
If the library is not installed this module is a no-op.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Iterator

from cappa.type_view import TypeView

annotated_types_bases = ()

if TYPE_CHECKING:
    import annotated_types

else:
    try:
        import annotated_types
    except ImportError:  # pragma: no cover
        annotated_types = None


def collect_validators(type_view: TypeView[Any]) -> list[Callable[[Any], Any]]:
    """Return validators derived from annotated-types metadata.

    Each validator accepts the already-parsed value, raises `ValueError` on
    constraint violation, and returns the value unchanged on success.
    """
    if not annotated_types:
        return []  # pragma: no cover

    validators: list[Callable[[Any], Any]] = []
    for meta in type_view.metadata:
        validators.extend(yield_validators(meta))
    return validators


def yield_validators(meta: Any) -> Iterator[Callable[[Any], Any]]:
    # Expand Annotated type aliases (e.g. annotated_types.IsDigits, LowerCase, UpperCase)
    # which are Annotated[TypeVar, Predicate(...)] rather than BaseMetadata instances.
    if hasattr(meta, "__metadata__"):
        for nested in meta.__metadata__:
            yield from yield_validators(nested)
        return

    if not isinstance(
        meta, (annotated_types.BaseMetadata, annotated_types.GroupedMetadata)
    ):
        return

    if isinstance(meta, annotated_types.GroupedMetadata):
        for item in meta:
            yield from yield_validators(item)
        return

    if isinstance(meta, annotated_types.Gt):
        yield validate_gt(meta.gt)
    elif isinstance(meta, annotated_types.Ge):
        yield validate_ge(meta.ge)
    elif isinstance(meta, annotated_types.Lt):
        yield validate_lt(meta.lt)
    elif isinstance(meta, annotated_types.Le):
        yield validate_le(meta.le)
    elif isinstance(meta, annotated_types.MultipleOf):
        yield validate_multiple_of(meta.multiple_of)
    elif isinstance(meta, annotated_types.MinLen):
        yield validate_min_len(meta.min_length)
    elif isinstance(meta, annotated_types.MaxLen):
        yield validate_max_len(meta.max_length)
    elif isinstance(meta, annotated_types.Predicate):
        yield validate_predicate(meta.func)
    elif isinstance(meta, annotated_types.Timezone):
        yield validate_timezone(meta.tz)  # pyright: ignore[reportUnknownMemberType]


def validate_gt(gt: Any) -> Callable[[Any], Any]:
    def _validate_gt(value: Any) -> Any:
        if not value > gt:
            raise ValueError(f"Expected value > {gt!r}, got {value!r}")
        return value

    return _validate_gt


def validate_ge(ge: Any) -> Callable[[Any], Any]:
    def _validate_ge(value: Any) -> Any:
        if not value >= ge:
            raise ValueError(f"Expected value >= {ge!r}, got {value!r}")
        return value

    return _validate_ge


def validate_lt(lt: Any) -> Callable[[Any], Any]:
    def _validate_lt(value: Any) -> Any:
        if not value < lt:
            raise ValueError(f"Expected value < {lt!r}, got {value!r}")
        return value

    return _validate_lt


def validate_le(le: Any) -> Callable[[Any], Any]:
    def _validate_le(value: Any) -> Any:
        if not value <= le:
            raise ValueError(f"Expected value <= {le!r}, got {value!r}")
        return value

    return _validate_le


def validate_multiple_of(multiple_of: Any) -> Callable[[Any], Any]:
    def _validate_multiple_of(value: Any) -> Any:
        if value % multiple_of != 0:
            raise ValueError(
                f"Expected value to be a multiple of {multiple_of!r}, got {value!r}"
            )
        return value

    return _validate_multiple_of


def validate_min_len(min_length: int) -> Callable[[Any], Any]:
    def _validate_min_len(value: Any) -> Any:
        if len(value) < min_length:
            raise ValueError(f"Expected length >= {min_length}, got {len(value)}")
        return value

    return _validate_min_len


def validate_max_len(max_length: int) -> Callable[[Any], Any]:
    def _validate_max_len(value: Any) -> Any:
        if len(value) > max_length:
            raise ValueError(f"Expected length <= {max_length}, got {len(value)}")
        return value

    return _validate_max_len


def validate_predicate(func: Callable[[Any], bool]) -> Callable[[Any], Any]:
    def _validate_predicate(value: Any) -> Any:
        if not func(value):
            raise ValueError(f"Expected {func!r} to return True for {value!r}")
        return value

    return _validate_predicate


def validate_timezone(tz: Any) -> Callable[[Any], Any]:
    def _validate_timezone(value: Any) -> Any:
        if not isinstance(value, datetime):
            return value

        if tz is None:
            if value.tzinfo is not None:
                raise ValueError(
                    f"Expected naive datetime (no timezone), got {value!r}"
                )
        elif tz is ...:
            if value.tzinfo is None:
                raise ValueError(f"Expected timezone-aware datetime, got {value!r}")
        else:
            if value.tzinfo is None:
                raise ValueError(
                    f"Expected datetime with timezone {tz!r}, got naive datetime"
                )

        return value

    return _validate_timezone
