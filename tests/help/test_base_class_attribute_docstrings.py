from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import pytest

from tests.utils import Backend, backends, parse, strip_trailing_whitespace


@dataclass
class Base:
    foo: int
    """This is a foo."""

    bar: str
    """This is a bar."""


@dataclass
class Child(Base):
    pass


@pytest.mark.help
@backends
def test_base_class_attribute_docstrings(backend: Backend, capsys: Any):
    with pytest.raises(SystemExit):
        parse(Child, "--help", backend=backend, completion=False)

    result = strip_trailing_whitespace(capsys.readouterr().out)
    assert re.match(r".*FOO\s+This is a foo\..*", result, re.DOTALL)
    assert re.match(r".*BAR\s+This is a bar\..*", result, re.DOTALL)
