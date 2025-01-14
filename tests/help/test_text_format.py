import sys
from dataclasses import dataclass

import pytest
from rich.console import Console
from rich.text import Text

import cappa
from tests.utils import backends, parse


@pytest.mark.help
@backends
def test_arg_renders_text(backend, capsys):
    @dataclass
    class Args:
        foo: str
        """[yellow]This is yellow[/]"""

    with pytest.raises(cappa.Exit):
        parse(
            Args,
            "--help",
            backend=backend,
            help_formatter=cappa.HelpFormatter().with_arg_format(
                Text("[red]Help:[/] {help}")
            ),
            output=cappa.Output(
                output_console=Console(force_terminal=True, file=sys.stdout)
            ),
        )

    result = capsys.readouterr()

    red = "\x1b[31m"
    yellow = "\x1b[33m"
    end = "\x1b[0m"

    expected_result = f"{red}Help:{end} {yellow}This is yellow{end}"
    assert expected_result in result.out

    assert str(Text.from_ansi(expected_result)) == "Help: This is yellow"


@pytest.mark.help
@backends
def test_arg_renders_string(backend, capsys):
    @dataclass
    class Args:
        foo: str
        """[yellow]This is yellow[/]"""

    with pytest.raises(cappa.Exit):
        parse(
            Args,
            "--help",
            backend=backend,
            help_formatter=cappa.HelpFormatter(arg_format="Help: {help}"),
            output=cappa.Output(
                output_console=Console(force_terminal=True, file=sys.stdout)
            ),
        )

    result = capsys.readouterr()

    yellow = "\x1b[33m"
    end = "\x1b[0m"

    expected_result = f"Help: {yellow}This is yellow{end}"
    assert expected_result in result.out

    assert str(Text.from_ansi(expected_result)) == "Help: This is yellow"
