import pytest

from cappa.class_inspect import FunctionField, fields


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
    """FunctionField.collect on top-level fn: unannotated first param, no '.' in qualname.

    Covers the False branch of ``if '.' in qualname`` — the param is skipped rather
    than auto-annotated with the parent class.
    """
    result = FunctionField.collect(top_level_fn_with_unannotated_first_param)  # type: ignore[arg-type]
    assert [f.name for f in result] == ["y"]
