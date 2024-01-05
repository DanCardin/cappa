import pytest
from cappa.class_inspect import ClassTypes


def test_invalid_class_base():
    class Random:
        ...

    with pytest.raises(ValueError) as e:
        ClassTypes.from_cls(Random)
    assert (
        "'test_invalid_class_base.<locals>.Random' is not a currently supported kind of class."
        in str(e.value)
    )
