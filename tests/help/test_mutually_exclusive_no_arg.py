from __future__ import annotations

import pytest
from typing_extensions import Annotated

import cappa
from cappa.output import Exit, rich_to_ansi
from tests.utils import Backend, backends, parse


@cappa.command
class Args:
    flag: Annotated[
        str,
        cappa.Arg(long="--blue", action=lambda: "blue", num_args=0),
        cappa.Arg(long="--red", action=lambda: "red", num_args=0),
        cappa.Arg(long="--green", action=lambda: "green", num_args=0),
    ] = "blue"


@backends
def test_help(backend: Backend):
    output = cappa.Output()
    with pytest.raises(Exit) as e:
        parse(Args, "--help", backend=backend)

    assert "[--blue, --red, --green]" in rich_to_ansi(
        output.output_console, e.value.message
    )

    result = parse(Args, "--blue", backend=backend)
    assert result.flag == "blue"

    result = parse(Args, "--red", backend=backend)
    assert result.flag == "red"

    with pytest.raises(Exit) as e:
        parse(Args, "--blue", "--red", backend=backend)
