import sys
from dataclasses import dataclass
from typing import Any

import pytest
from rich.console import Console
from typing_extensions import Annotated

import cappa
from tests.utils import (
    Backend,
    backends,
    parse,
    strip_trailing_whitespace,
    terminal_width,
)


@pytest.mark.help
@backends
def test_arg_description_renders_markdown(backend: Backend, capsys: Any):
    @dataclass
    class Args:
        foo: str
        """`This` **is** _neat_"""

    with pytest.raises(cappa.Exit):
        parse(Args, "--help", backend=backend)

    result = capsys.readouterr()

    assert "This is neat" in result.out

    with pytest.raises(cappa.Exit):
        parse(
            Args,
            "--help",
            backend=backend,
            output=cappa.Output(
                output_console=Console(force_terminal=True, file=sys.stdout)
            ),
        )

    result = capsys.readouterr()
    assert "This\x1b[0m" in result.out
    assert " \x1b[1mis\x1b[0m" in result.out  # typos: ignore
    assert " \x1b[3mneat\x1b[0m" in result.out


@pytest.mark.help
@backends
def test_multi_paragraph_arg_help_preserves_paragraph_breaks(
    backend: Backend, capsys: Any
):
    @dataclass
    class Args:
        foo: Annotated[
            str,
            cappa.Arg(
                help="First paragraph summary.\n\nSecond paragraph body.",
            ),
        ]

    with terminal_width(80), pytest.raises(cappa.Exit):
        parse(Args, "--help", backend=backend)

    out = strip_trailing_whitespace(capsys.readouterr().out)

    assert "First paragraph summary." in out
    assert "Second paragraph body." in out

    summary_pos = out.index("First paragraph summary.")
    body_pos = out.index("Second paragraph body.")
    between = out[summary_pos + len("First paragraph summary.") : body_pos]
    assert "\n\n" in between


@pytest.mark.help
@backends
def test_soft_line_breaks_fold_into_spaces(backend: Backend, capsys: Any):
    @dataclass
    class SoftBreakArgs:
        foo: str
        """
        This is a long sentence that goes on and on.
        This second soft-break line continues the same paragraph.
        """

    with terminal_width(80), pytest.raises(cappa.Exit):
        parse(SoftBreakArgs, "--help", backend=backend, completion=False)

    out = strip_trailing_whitespace(capsys.readouterr().out)

    # Words from adjacent soft-break lines must be separated by a space
    assert "on.This" not in out
    assert "on. This" in out

    # And must not have a blank line between them (same paragraph)
    first = out.index("goes on and on.")
    second = out.index("same paragraph.")
    assert "\n\n" not in out[first:second]
