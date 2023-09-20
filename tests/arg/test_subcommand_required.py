from __future__ import annotations

from dataclasses import dataclass
from typing import Union

import cappa
import pytest
from typing_extensions import Annotated

from tests.utils import parse


@dataclass
class Command:
    subcmd: Annotated[Union[A, None], cappa.Subcommand(required=True)] = None


@dataclass
class A:
    ...


def test_required_implicit():
    with pytest.raises(ValueError, match=r"are required: {a}"):
        parse(Command)

    result = parse(Command, "a")
    assert result == Command(subcmd=A())
