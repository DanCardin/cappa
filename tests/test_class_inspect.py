import pytest

from cappa.class_inspect import _collect_function, fields  # pyright: ignore


def top_level_fn_with_unannotated_first_param(x, y: str) -> str:  # pyright: ignore
    return y


def test_invalid_class_base():
    class Random: ...

    with pytest.raises(ValueError) as e:
        fields(Random)
    assert (
        "'test_invalid_class_base.<locals>.Random' is not a currently supported kind of class."
        in str(e.value)
    )


def test_function_field_collect_unannotated_first_param_no_dot_qualname():
    """Unannotated first param, no '.' in qualname should be skipped."""
    result = _collect_function(top_level_fn_with_unannotated_first_param)  # type: ignore[arg-type]
    assert [f.name for f in result] == ["y"]
