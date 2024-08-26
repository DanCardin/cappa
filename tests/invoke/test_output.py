from __future__ import annotations

from dataclasses import dataclass

import cappa
from tests.utils import backends, invoke


@dataclass
class TopLevelCommand:
    def __call__(self, out: cappa.Output):
        out.output("woah!")
        out.error("woops!")


@backends
def test_outputs_output(backend, capsys):
    invoke(TopLevelCommand, backend=backend)

    outerr = capsys.readouterr()
    assert outerr.out == "woah!\n"
    assert outerr.err == "Error: woops!\n"
