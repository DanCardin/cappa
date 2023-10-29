import re
from dataclasses import dataclass
from textwrap import dedent

import cappa
import pytest

from tests.utils import (
    backends,
    ignore_docstring_parser,
    parse,
    strip_trailing_whitespace,
)


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


@pytest.mark.help
@backends
def test_docstring_being_used_but_not_parsed(backend, capsys, monkeypatch):
    @dataclass
    class UnparsedDocstring:
        """Summary.

        Example:
         - one
        """

    with pytest.raises(cappa.Exit), ignore_docstring_parser(monkeypatch):
        parse(UnparsedDocstring, "--help", backend=backend, completion=False)

    result = strip_trailing_whitespace(capsys.readouterr().out)

    assert result == dedent(
        """\
        Usage: unparsed-docstring [-h]

          Summary.
        
          Example:

           • one

          Help
            [-h, --help]  Show this message and exit.
        """
    )


@pytest.mark.help
@backends
def test_docstring_being_used_but_not_parsed_one_line(backend, capsys, monkeypatch):
    @dataclass
    class UnparsedDocstring:
        """Summary."""

    with pytest.raises(cappa.Exit), ignore_docstring_parser(monkeypatch):
        parse(UnparsedDocstring, "--help", backend=backend, completion=False)

    result = strip_trailing_whitespace(capsys.readouterr().out)
    assert result == dedent(
        """\
        Usage: unparsed-docstring [-h]

          Summary.

          Help
            [-h, --help]  Show this message and exit.
        """
    )
