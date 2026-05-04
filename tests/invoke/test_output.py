from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import Backend, CapsysOutput, backends, invoke


@backends
def test_outputs_output(backend: Backend, capsys: Any):
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
def test_output_callable(backend: Backend, capsys: Any):
    @dataclass
    class TopLevelCommand:
        def __call__(self, out: cappa.Output):
            out("woah!")

    invoke(TopLevelCommand, backend=backend)

    out = CapsysOutput.from_capsys(capsys)
    out.stdout = "woah!\n"
    out.stderr = ""


def _raise_value_error(value: str) -> str:
    raise ValueError("nope")


@backends
def test_invoke_routes_parse_errors_through_output(backend: Backend, capsys: Any):
    """A parse= callback that raises should produce a visible error on stderr.

    Regression test: previously `invoke()` (and `invoke_async`/`parse`) did not
    pass `output=` into the resolution of `parse_result.instance`, so any
    `cappa.Exit` raised from an `Arg(parse=...)` callback would be caught by
    `Resolved.handle_exit` with `output=None` and silently re-raised, producing
    a non-zero exit with no message.
    """

    @dataclass
    class Cmd:
        x: Annotated[
            str,
            cappa.Arg(parse=_raise_value_error, parse_inference=False, long="--x"),
        ] = "default"

        def __call__(self) -> None:
            pass

    with pytest.raises(cappa.Exit) as e:
        invoke(Cmd, "--x", "foo", backend=backend)

    assert e.value.code == 2
    out = CapsysOutput.from_capsys(capsys)
    assert "Invalid value for '--x': nope" in out.stderr
