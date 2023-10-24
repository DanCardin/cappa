import re
from dataclasses import dataclass

import cappa
import pytest

from tests.utils import backends, parse


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


@pytest.mark.help
@backends
def test_required_provided(backend, capsys):
    with pytest.raises(cappa.Exit):
        parse(IncludesDocstring, "--help", backend=backend)

    result = capsys.readouterr().out

    assert "[--bar] FOO [-h]" in result
    assert re.match(r".*Does a thing\.\s+and does it really well!.*", result, re.DOTALL)
    assert re.match(r".*FOO\s+the value of foo.*", result, re.DOTALL)
    assert re.match(r".*\[--bar\]\s+whether to bar.*", result, re.DOTALL)


@pytest.mark.help
@backends
def test_just_a_title(backend, capsys):
    @dataclass
    class IncludesDocstring:
        """Just a title."""

    with pytest.raises(cappa.Exit):
        parse(IncludesDocstring, "--help", backend=backend)

    result = capsys.readouterr().out

    assert "Just a title" in result


@pytest.mark.help
@backends
def test_docstring_with_explicit_help(backend, capsys):
    @cappa.command(help="help text")
    @dataclass
    class IncludesDocstring:
        """Just a title."""

    with pytest.raises(cappa.Exit):
        parse(IncludesDocstring, "--help", backend=backend)

    result = capsys.readouterr().out

    assert "Just a title" not in result
    assert "help text" in result


@pytest.mark.help
@backends
def test_docstring_with_explicit_description(backend, capsys):
    @cappa.command(description="description")
    @dataclass
    class IncludesDocstring:
        """Just a title."""

    with pytest.raises(cappa.Exit):
        parse(IncludesDocstring, "--help", backend=backend)

    result = capsys.readouterr().out

    assert "Just a title" in result
    assert "description" in result
