from __future__ import annotations

import sys
import textwrap
from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import parse


def test_native_backend(capsys):
    @dataclass
    class ArgTest:
        arg1: Annotated[str, cappa.Arg(deprecated=True)] = "default"
        arg2: Annotated[str, cappa.Arg(short="a", long="--aaaa", deprecated=True)] = (
            "default"
        )
        arg3: Annotated[str, cappa.Arg(short="b", deprecated="Use something else")] = (
            "default"
        )

    result = parse(ArgTest)
    assert result.arg1 == "default"
    assert result.arg2 == "default"
    assert result.arg3 == "default"
    err = capsys.readouterr().err
    assert err == ""

    result = parse(ArgTest, "a")
    assert result.arg1 == "a"
    err = capsys.readouterr().err
    assert err == "Error: Argument `arg1` is deprecated\n"

    result = parse(ArgTest, "-a", "1")
    assert result.arg2 == "1"
    err = capsys.readouterr().err
    assert err == "Error: Option `-a` is deprecated\n"

    result = parse(ArgTest, "-b", "1")
    assert result.arg3 == "1"
    err = capsys.readouterr().err
    assert err == "Error: Option `-b` is deprecated: Use something else\n"


@pytest.mark.skipif(sys.version_info >= (3, 13), reason="requires python3.13 or higher")
def test_argparse_le_313(capsys):
    """Below 3.13, this option has no effect."""

    @dataclass
    class ArgTest:
        arg1: Annotated[str, cappa.Arg(deprecated=True)] = "default"
        arg2: Annotated[str, cappa.Arg(short="a", long="--aaaa", deprecated=True)] = (
            "default"
        )
        arg3: Annotated[str, cappa.Arg(short="b", deprecated="Use something else")] = (
            "default"
        )

    result = parse(ArgTest, backend=cappa.argparse.backend)
    assert result.arg1 == "default"
    assert result.arg2 == "default"
    assert result.arg3 == "default"
    err = capsys.readouterr().err
    assert err == ""

    result = parse(ArgTest, "1", "-a", "1", "-b", "1", backend=cappa.argparse.backend)
    assert result.arg1 == "1"
    assert result.arg1 == "1"
    assert result.arg1 == "1"
    err = capsys.readouterr().err
    assert err == ""


@pytest.mark.skipif(
    sys.version_info < (3, 13), reason="Below 3.13, the behavior is different"
)
def test_argparse_ge_313(capsys):
    @dataclass
    class ArgTest:
        arg1: Annotated[str, cappa.Arg(deprecated=True)] = "default"
        arg2: Annotated[str, cappa.Arg(short="a", long="--aaaa", deprecated=True)] = (
            "default"
        )
        arg3: Annotated[str, cappa.Arg(short="b", deprecated="Use something else")] = (
            "default"
        )

    result = parse(ArgTest, backend=cappa.argparse.backend)
    assert result.arg1 == "default"
    assert result.arg2 == "default"
    assert result.arg3 == "default"
    err = capsys.readouterr().err
    assert err == ""

    result = parse(ArgTest, "1", "-a", "1", "-b", "1", backend=cappa.argparse.backend)
    assert result.arg1 == "1"
    assert result.arg1 == "1"
    assert result.arg1 == "1"
    err = capsys.readouterr().err.replace("arg-test: ", "")
    assert err == textwrap.dedent(
        """\
        warning: argument 'arg1' is deprecated
        warning: option '-a' is deprecated
        warning: option '-b' is deprecated
        """
    )
