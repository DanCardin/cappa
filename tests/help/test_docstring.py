import re
from dataclasses import dataclass
from textwrap import dedent

import pytest

import cappa
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


@pytest.mark.help
@backends
def test_escaped_markdown(backend, capsys, monkeypatch):
    @dataclass
    class Escaped:
        """Blabla.

        And configure `~/.pypirc`:

        ```ini
        [distutils]
        index-servers =
            pypi
        ```
        """

    with pytest.raises(cappa.Exit), ignore_docstring_parser(monkeypatch):
        parse(Escaped, "--help", backend=backend, completion=False)

    result = strip_trailing_whitespace(capsys.readouterr().out)
    assert result == dedent(
        """\
        Usage: escaped [-h]

          Blabla.
          
          And configure ~/.pypirc:
          
          
           [distutils]
           index-servers =
               pypi


          Help
            [-h, --help]  Show this message and exit.
        """
    )


@pytest.mark.help
@backends
def test_attribute_docstring(backend, capsys):
    @dataclass
    class Args:
        """Bah.

        Arguments:
            top_level: woo woo
            foo: this should get superseded
        """

        top_level: int

        foo: int
        """This is a foo."""

        bar: str
        """This is a bar."""

    with pytest.raises(cappa.Exit):
        parse(Args, "--help", backend=backend, completion=False)

    result = strip_trailing_whitespace(capsys.readouterr().out)
    assert result == dedent(
        """\
        Usage: args TOP_LEVEL FOO BAR [-h]

          Bah.

          Arguments
            TOP_LEVEL     woo woo
            FOO           This is a foo.
            BAR           This is a bar.

          Help
            [-h, --help]  Show this message and exit.
        """
    )


@pytest.mark.help
@backends
def test_explicit_help_description_manual_args(backend, capsys):
    @cappa.command(help="Title", description="longer description")
    @dataclass
    class Args2:
        """...

        Args:
            foo: nope
            bar: yep
        """

        foo: int
        """this is a foo"""

        bar: int

    with pytest.raises(cappa.Exit):
        parse(Args2, "--help", backend=backend, completion=False)

    result = strip_trailing_whitespace(capsys.readouterr().out)
    assert result == dedent(
        """\
        Usage: args2 FOO BAR [-h]

          Title

          longer description

          Arguments
            FOO           this is a foo
            BAR           yep

          Help
            [-h, --help]  Show this message and exit.
        """
    )
