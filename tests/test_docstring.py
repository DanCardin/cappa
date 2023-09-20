from dataclasses import dataclass

import pytest

from tests.utils import parse


@dataclass
class IncludesDocstring:
    """Does a thing.

    and does it really well!

    Args:
        foo (str): the value of foo
        bar (bool): whether to bar
    """

    foo: str
    bar: bool = False


def test_required_provided(capsys):
    with pytest.raises(ValueError):
        parse(IncludesDocstring, "--help")

    result = capsys.readouterr().out

    assert "[--bar] [-h] foo" in result
    assert "Does a thing. and does it really well!" in result
    assert "foo         the value of foo" in result
    assert "--bar       whether to bar (default: False)" in result
