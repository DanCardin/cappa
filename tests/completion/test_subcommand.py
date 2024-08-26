from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from typing_extensions import Annotated

import cappa
from tests.utils import parse_completion


@dataclass
class Foo: ...


@dataclass
class Bar:
    nested_opt: Annotated[str, cappa.Arg(long=True)]


@dataclass
class Args:
    value: cappa.Subcommands[Union[Foo, Bar]]


def test_subcommand_name_no_partial():
    result = parse_completion(Args, "")
    assert result == "foo:\nbar:"


def test_subcommand_name_with_partial():
    result = parse_completion(Args, "f")
    assert result
    assert result == "foo:"


def test_subcommand_args():
    result = parse_completion(Args, "bar", "--n")
    assert result
    assert result == "--nested-opt:"
