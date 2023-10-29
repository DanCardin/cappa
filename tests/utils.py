import contextlib
from typing import Union
from unittest.mock import patch

import pytest
from cappa import argparse, parser
from cappa.output import Exit
from cappa.testing import CommandRunner

backends = pytest.mark.parametrize("backend", [None, argparse.backend])

runner = CommandRunner(base_args=[])


def parse(cls, *args, **kwargs):
    return runner.parse(*args, obj=cls, **kwargs)


def invoke(cls, *args, **kwargs):
    return runner.invoke(*args, obj=cls, **kwargs)


def parse_completion(cls, *args, location=None) -> Union[str, None]:
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
def ignore_docstring_parser(monkeypatch):
    import importlib

    cappa_command = importlib.import_module("cappa.command")

    with monkeypatch.context() as m:
        m.setattr(cappa_command, "docstring_parser", None)
        yield


def strip_trailing_whitespace(text):
    return "\n".join([line.rstrip() for line in text.split("\n")])
