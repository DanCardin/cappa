from __future__ import annotations

from dataclasses import dataclass
from typing import Union

import cappa
import pytest
from typing_extensions import Annotated

from tests.utils import parse


@dataclass
class RequiredMissingOne:
    foo: Annotated[Union[str, None], cappa.Arg(long=True)] = None


@dataclass
class RequiredMissing:
    subcommand: Annotated[RequiredMissingOne, cappa.Subcommand]


def test_required_missing():
    with pytest.raises(
        Exception, match=r"following arguments are required: {required-missing-one}"
    ):
        parse(RequiredMissing)


@dataclass
class RequiredProvidedOne:
    foo: Annotated[Union[str, None], cappa.Arg(long=True)] = None


@dataclass
class RequiredProvidedTwo:
    bar: Annotated[Union[str, None], cappa.Arg(long=True)] = None


@dataclass
class RequiredProvided:
    subcommand: Annotated[
        Union[RequiredProvidedOne, RequiredProvidedTwo], cappa.Subcommand()
    ]


def test_required_provided():
    test = parse(RequiredProvided, "required-provided-one", "--foo", "foo")
    assert isinstance(test.subcommand, RequiredProvidedOne)
    assert test.subcommand.foo == "foo"

    test = parse(RequiredProvided, "required-provided-two")
    assert isinstance(test.subcommand, RequiredProvidedTwo)
    assert test.subcommand.bar is None

    test = parse(RequiredProvided, "required-provided-two", "--bar", "bar")
    assert isinstance(test.subcommand, RequiredProvidedTwo)
    assert test.subcommand.bar == "bar"


@cappa.command(name="one")
@dataclass
class NamedSubcommandOne:
    pass


@dataclass
class NamedSubcommand:
    subcommand: Annotated[NamedSubcommandOne, cappa.Subcommand()]


def test_named_subcommand():
    test = parse(NamedSubcommand, "one")
    assert isinstance(test.subcommand, NamedSubcommandOne)
