from __future__ import annotations

from dataclasses import dataclass
from typing import Union

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import parse


@dataclass
class RequiredMissingOne:
    foo: Annotated[Union[str, None], cappa.Arg(long=True)] = None


@dataclass
class RequiredMissingTwo:
    foo: Annotated[Union[str, None], cappa.Arg(long=True)] = None


@dataclass
class RequiredMissing:
    subcommand: Annotated[
        Union[RequiredMissingOne, RequiredMissingTwo], cappa.Subcommand
    ]


def test_has_possible_values():
    with pytest.raises(cappa.Exit) as e:
        parse(RequiredMissing, "req", backend=None)
    assert isinstance(e.value.message, str)

    expected_message = (
        "Invalid command 'req' (Did you mean: "
        "[cappa.subcommand]required-missing-one[/cappa.subcommand], "
        "[cappa.subcommand]required-missing-two[/cappa.subcommand])"
    )
    assert expected_message == e.value.message


def test_no_possible_values():
    with pytest.raises(cappa.Exit) as e:
        parse(RequiredMissing, "bad", backend=None)
    assert isinstance(e.value.message, str)

    expected_message = "Invalid command 'bad'"
    assert expected_message == e.value.message
