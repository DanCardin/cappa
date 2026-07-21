from __future__ import annotations

from dataclasses import dataclass

from cappa.docstring import get_attribute_docstrings


def test_attribute_docstring_single_line():
    @dataclass
    class Args:
        foo: int
        """A simple description."""

    result = get_attribute_docstrings(Args)
    assert result == {"foo": "A simple description."}


def test_attribute_docstring_indented_multiline():
    @dataclass
    class Args:
        foo: int
        """First paragraph.

        Second paragraph.
        """

    result = get_attribute_docstrings(Args)
    assert result == {"foo": "First paragraph.\n\nSecond paragraph."}


def test_attribute_docstring_indented_multiline_dedented():
    """Indented attribute docstrings must not be treated as Markdown code blocks."""

    @dataclass
    class Args:
        foo: int
        """Summary line.

        Body paragraph that would have 8 spaces of indent before cleandoc,
        with a long enough body to wrap.
        """

    result = get_attribute_docstrings(Args)

    # No leading spaces on continuation lines
    assert not any(line.startswith("    ") for line in result["foo"].splitlines())
