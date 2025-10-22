from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from typing_extensions import Annotated

import cappa
from cappa.output import Exit
from tests.utils import (
    Backend,
    CapsysOutput,
    backends,
    parse,
    terminal_width,
)


@dataclass
class Args:
    verbose: Annotated[
        int,
        cappa.Arg(short="-v", help="All help is included."),
        cappa.Arg(long="--verbosity", help="But the default is not duplicated"),
    ] = 0


@backends
def test_help(backend: Backend, capsys: Any):
    with terminal_width(), pytest.raises(Exit):
        parse(Args, "--help", backend=backend)

    out = CapsysOutput.from_capsys(capsys)
    assert "All help is included. But the default is not duplicated" in out.stdout
    assert "(Default: 0)" in out.stdout
