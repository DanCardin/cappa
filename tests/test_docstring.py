from dataclasses import dataclass

import cappa
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


@pytest.mark.help
def test_required_provided(capsys):
    with pytest.raises(cappa.Exit):
        parse(IncludesDocstring, "--help")

    result = capsys.readouterr().out

    assert "[--bar] [-h] foo" in result
    assert "Does a thing. and does it really well!" in result
    assert "foo         the value of foo" in result
    assert "--bar       whether to bar (default: False)" in result


@pytest.mark.help
def test_just_a_title(capsys):
    @dataclass
    class IncludesDocstring:
        """Just a title."""

    with pytest.raises(cappa.Exit):
        parse(IncludesDocstring, "--help")

    result = capsys.readouterr().out

    assert "Just a title" in result


@pytest.mark.help
def test_docstring_with_explicit_help(capsys):
    @cappa.command(help="help text")
    @dataclass
    class IncludesDocstring:
        """Just a title."""

    with pytest.raises(cappa.Exit):
        parse(IncludesDocstring, "--help")

    result = capsys.readouterr().out

    assert "Just a title" not in result
    assert "help text" in result


@pytest.mark.help
def test_docstring_with_explicit_description(capsys):
    @cappa.command(description="description")
    @dataclass
    class IncludesDocstring:
        """Just a title."""

    with pytest.raises(cappa.Exit):
        parse(IncludesDocstring, "--help")

    result = capsys.readouterr().out

    assert "Just a title" in result
    assert "description" in result
