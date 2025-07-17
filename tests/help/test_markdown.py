import sys
from dataclasses import dataclass
from typing import Any

import pytest
from rich.console import Console

import cappa
from tests.utils import Backend, backends, parse


@pytest.mark.help
@backends
def test_arg_description_renders_markdown(backend: Backend, capsys: Any):
    @dataclass
    class Args:
        foo: str
        """`This` **is** _neat!_"""

    with pytest.raises(cappa.Exit):
        parse(Args, "--help", backend=backend)

    result = capsys.readouterr()

    assert "This is neat!" in result.out

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
    assert (
        "\x1b[1;36;40mThis\x1b[0m \x1b[1mis\x1b[0m \x1b[3mneat!\x1b[0m"  # typos: ignore
        in result.out
    )
