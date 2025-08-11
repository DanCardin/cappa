from __future__ import annotations

from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from cappa.subcommand import Subcommands
from tests.utils import parse


@dataclass
class SubSub:
    foo: int


@dataclass
class InvalidSubcommandSub:
    sub: Subcommands[SubSub]


@dataclass
class InvalidSubcommand:
    attrs: Annotated[InvalidSubcommandSub, cappa.Arg.destructured()]


def test_invalid_subcommand():
    with pytest.raises(ValueError) as e:
        parse(InvalidSubcommand)
    assert (
        str(e.value)
        == "Subcommands are unsupported in the context of a destructured argument"
    )
