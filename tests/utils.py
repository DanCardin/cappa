from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Any, Union
from unittest.mock import patch

import pytest
from typing_extensions import Unpack

from cappa import argparse, parser
from cappa.base import Backend
from cappa.command import Command
from cappa.invoke import DepTypes, InvokeCallable
from cappa.output import Exit
from cappa.testing import CommandRunner, RunnerArgs, T

__all__ = [
    "Backend",
    "CapsysOutput",
    "backends",
    "invoke",
    "invoke_async",
    "parse",
    "runner",
]

backends = pytest.mark.parametrize("backend", [None, argparse.backend])

runner: CommandRunner[Any] = CommandRunner(base_args=[])


def parse(
    cls: type[T] | InvokeCallable[T] | Command[T],
    *args: str,
    **kwargs: Unpack[RunnerArgs],
) -> T:
    return runner.parse(cls, *args, **kwargs)


def invoke(
    cls: type[T] | InvokeCallable[T] | Command[T],
    *args: str,
    deps: DepTypes | None = None,
    **kwargs: Unpack[RunnerArgs],
):
    return runner.invoke(cls, *args, deps=deps, **kwargs)


def invoke_async(
    cls: type[T] | InvokeCallable[T] | Command[T],
    *args: str,
    deps: DepTypes | None = None,
    **kwargs: Unpack[RunnerArgs],
):
    return runner.invoke_async(cls, *args, deps=deps, **kwargs)


def parse_completion(
    cls: type, *args: str, location: str | None = None
) -> Union[str, None]:
    env = {
        "COMPLETION_LINE": " ".join(["test.py", *args]),
        "COMPLETION_LOCATION": location if location is not None else len(args) + 1,
    }
    with patch("os.environ", new=env):
        with pytest.raises(Exit) as e:
            parse(cls, "--completion", "complete", backend=parser.backend)

        assert e.value.code == 0
        if e.value.message:
            return str(e.value.message)
        return None


@contextlib.contextmanager
def ignore_docstring_parser(monkeypatch: Any):
    import importlib

    cappa_command = importlib.import_module("cappa.docstring")

    with monkeypatch.context() as m:
        m.setattr(cappa_command, "docstring_parser", None)
        yield


def strip_trailing_whitespace(text: str):
    return "\n".join([line.rstrip() for line in text.split("\n")])


@dataclass
class CapsysOutput:
    stdout: str
    stderr: str

    @classmethod
    def from_capsys(cls, capsys: Any):
        outerr = capsys.readouterr()

        out = strip_trailing_whitespace(outerr.out)
        err = strip_trailing_whitespace(outerr.err)
        return cls(out, err)
