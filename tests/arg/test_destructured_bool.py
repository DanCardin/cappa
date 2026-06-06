from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent
from typing import Any

import pytest

import cappa
from tests.utils import (
    Backend,
    backends,
    parse,
    strip_trailing_whitespace,
    terminal_width,
)


@dataclass
class Flags:
    flag: bool = False
    enabled: bool = True


@dataclass
class Args:
    flags: cappa.Destructured[Flags]


@backends
def test_bool_destructured(backend: Backend, capsys: Any):
    assert parse(Args, "--flag") == Args(flags=Flags(flag=True, enabled=True))
    assert parse(Args, "--enabled") == Args(flags=Flags(flag=False, enabled=False))

    with terminal_width(80), pytest.raises(cappa.Exit):
        parse(Args, "--help", backend=backend, completion=False)

    result = strip_trailing_whitespace(capsys.readouterr().out)
    assert result == dedent(
        """\
        Usage: args [--flag] [--enabled] [-h]

          Options
            [--flag]      (Default: False)
            [--enabled]   (Default: True)

          Help
            [-h, --help]  Show this message and exit.
        """
    )
