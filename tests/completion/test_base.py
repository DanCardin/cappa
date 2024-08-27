from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import pytest

import cappa
from cappa.parser import backend
from tests.utils import parse


def test_unknown_shell():
    @dataclass
    class Args:
        value: str

    with patch("os.environ", new={"SHELL": "notbash"}):
        with pytest.raises(cappa.Exit) as e:
            parse(Args, "--completion", "complete", backend=backend)

    assert e.value.code == 1
    assert e.value.message == "Unknown shell"


def test_generate_completions():
    @dataclass
    class Args:
        value: str

    with pytest.raises(cappa.Exit) as e:
        parse(Args, "--completion", "generate", backend=backend)

    assert e.value.code == 0
    assert e.value.message
    assert "_args_completion" in str(e.value.message)


def test_invalid_setup():
    @dataclass
    class Args:
        value: str

    with pytest.raises(cappa.Exit) as e:
        parse(Args, "--completion", "complete", backend=backend)

    assert e.value.code == 0
    assert not e.value.message


def test_no_completion():
    @dataclass
    class Example: ...

    result = cappa.parse(Example, argv=[], backend=backend, completion=False)
    assert result == Example()

    with pytest.raises(cappa.Exit) as e:
        cappa.parse(
            Example,
            argv=["--completion", "generate"],
            backend=backend,
            completion=False,
        )
    assert e.value.code == 2


def test_arg_completion(capsys):
    @dataclass
    class Example: ...

    completion: cappa.Arg = cappa.Arg(short="-p", long="--pompletion")

    result = cappa.parse(Example, argv=[], completion=completion, backend=backend)
    assert result == Example()

    with pytest.raises(SystemExit) as e:
        cappa.parse(
            Example,
            argv=["-p", "generate"],
            completion=completion,
            backend=backend,
        )
    assert e.value.code == 0

    out = capsys.readouterr().out
    assert "_example_completion" in out

    with pytest.raises(SystemExit) as e:
        cappa.parse(
            Example,
            argv=["--help"],
            completion=completion,
            backend=backend,
        )
    assert e.value.code == 0

    out = capsys.readouterr().out
    assert "-p, --pompletion" in out
