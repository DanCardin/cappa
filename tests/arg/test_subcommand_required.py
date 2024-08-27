from __future__ import annotations

from dataclasses import dataclass
from typing import Union

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@dataclass
class Command:
    subcmd: Annotated[Union[A, None], cappa.Subcommand(required=True)] = None


@dataclass
class A: ...


@backends
def test_required_implicit(backend):
    with pytest.raises(cappa.Exit) as e:
        parse(Command)
    assert e.value.code == 2
    assert "A command is required: {[cappa.subcommand]a[/cappa.subcommand]}" in str(
        e.value.message
    )

    result = parse(Command, "a", backend=backend)
    assert result == Command(subcmd=A())
