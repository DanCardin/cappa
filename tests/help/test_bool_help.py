from __future__ import annotations

import re
from typing import Any

import pytest
from typing_extensions import Annotated

import cappa
from cappa.output import Exit
from tests.utils import Backend, CapsysOutput, backends, parse


@cappa.command
class Args:
    flag: Annotated[bool, cappa.Arg(long=["--flag", "--no-flag"], help="meow.")] = False


@pytest.mark.help
@backends
def test_default_help(backend: Backend, capsys: Any):
    with pytest.raises(Exit):
        parse(Args, "--help", backend=backend)

    out = CapsysOutput.from_capsys(capsys)
    assert re.match(r".*--no-flag]\s+meow.\s+\(Default", out.stdout, re.DOTALL)
