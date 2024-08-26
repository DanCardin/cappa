from __future__ import annotations

import sys
from dataclasses import dataclass

import pytest

import cappa
from tests.utils import parse


@cappa.command(deprecated=True)
@dataclass
class Sub:
    pass


@dataclass
class ArgTest:
    sub: cappa.Subcommands[Sub | None] = None


def test_native_backend(capsys):
    """Note, argparse only support deprecated at or above 3.13."""
    result = parse(ArgTest)
    assert result.sub is None
    err = capsys.readouterr().err
    assert err == ""

    result = parse(ArgTest, "sub")
    assert result.sub == Sub()
    err = capsys.readouterr().err
    assert err == "Error: Command `sub` is deprecated\n"


@pytest.mark.skipif(sys.version_info >= (3, 13), reason="requires python3.13 or higher")
def test_argparse_le_313(capsys):
    """Below 3.13, this option has no effect."""
    result = parse(ArgTest, backend=cappa.argparse.backend)
    assert result.sub is None
    err = capsys.readouterr().err
    assert err == ""

    result = parse(ArgTest, "sub", backend=cappa.argparse.backend)
    assert result.sub == Sub()
    err = capsys.readouterr().err
    assert err == ""


@pytest.mark.skipif(
    sys.version_info < (3, 13), reason="Below 3.13, the behavior is different"
)
def test_argparse_ge_313(capsys):
    result = parse(ArgTest, backend=cappa.argparse.backend)
    assert result.sub is None
    err = capsys.readouterr().err
    assert err == ""

    result = parse(ArgTest, "sub", backend=cappa.argparse.backend)
    assert result.sub == Sub()
    err = capsys.readouterr().err.replace("arg-test: ", "").strip()
    assert err == "warning: command 'sub' is deprecated"
