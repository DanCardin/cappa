import contextlib
import io
import textwrap
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


def test_required_provided():
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), pytest.raises(ValueError):
        parse(IncludesDocstring, "--help")

    text = buffer.getvalue()
    _, _, result = text.split(" ", 2)

    expected_result = textwrap.dedent(
        """\
        [-h] [--bar] foo

        Does a thing. and does it really well!

        positional arguments:
          foo         the value of foo

        options:
          -h, --help  show this help message and exit
          --bar       whether to bar
        """
    )
    assert result == expected_result
