from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cappa
from tests.utils import CapsysOutput, backends, invoke


@backends
def test_outputs_output(backend, capsys):
    @dataclass
    class TopLevelCommand:
        def __call__(self, out: cappa.Output):
            out.output("woah!")
            out.error("woops!")

    invoke(TopLevelCommand, backend=backend)

    outerr = capsys.readouterr()
    assert outerr.out == "woah!\n"
    assert outerr.err == "Error: woops!\n"


@backends
def test_output_callable(backend, capsys: Any):
    @dataclass
    class TopLevelCommand:
        def __call__(self, out: cappa.Output):
            out("woah!")

    invoke(TopLevelCommand, backend=backend)

    out = CapsysOutput.from_capsys(capsys)
    out.stdout = "woah!\n"
    out.stderr = ""
