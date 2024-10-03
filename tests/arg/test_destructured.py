from __future__ import annotations

import enum
from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from cappa.subcommand import Subcommands
from tests.utils import parse


class Flavor(enum.Enum):
    vanilla = "vanilla"
    chocolate = "chocolate"


@dataclass
class Attributes:
    color: Annotated[str, cappa.Arg(long="attribute.color")]
    flavors: Annotated[list[Flavor], cappa.Arg(value_name="attribute.flavor")]
    something: Annotated[int, cappa.Arg(short="-p")]
    custom_parse: Annotated[str, cappa.Arg(long="foo", parse=lambda _: "always this")]
    custom_action: Annotated[int, cappa.Arg(long="bar", action=lambda: 42)]
    optional: Annotated[int, cappa.Arg(long="baz")] = 4


@dataclass
class Args:
    attrs: Annotated[Attributes, cappa.Arg.destructure()]


def test_destructured():
    test = parse(
        Args,
        "--attribute.color=red",
        "chocolate",
        "vanilla",
        "-p4",
        "--foo=whatever",
        "--bar=0",
    )
    assert test == Args(
        attrs=Attributes(
            "red",
            [Flavor.chocolate, Flavor.vanilla],
            something=4,
            custom_parse="always this",
            custom_action=42,
            optional=4,
        )
    )


@dataclass
class OptionalArgs:
    attrs: Annotated[Attributes | None, cappa.Arg.destructure()]


def test_destructured_optional():
    with pytest.raises(ValueError) as e:
        parse(OptionalArgs)
    assert (
        str(e.value)
        == "Destructured arguments currently only support singular concrete types."
    )


@dataclass
class InvalidSubcommandSub:
    sub: Subcommands[Attributes]


@dataclass
class InvalidSubcommand:
    attrs: Annotated[InvalidSubcommandSub, cappa.Arg.destructure()]


def test_invalid_subcommand():
    with pytest.raises(ValueError) as e:
        parse(InvalidSubcommand)
    assert (
        str(e.value)
        == "Subcommands are unsupported in the context of a destructured argument"
    )


@dataclass
class CollisionSub:
    field1: str = ""
    field2: Annotated[str, cappa.Arg(long=True)] = ""


@dataclass
class Collision:
    sub: Annotated[CollisionSub, cappa.Arg.destructure()]
    field1: int = 0
    field2: int = 0


def test_destructured_collision():
    result = parse(Collision, "1")
    assert result == Collision(sub=CollisionSub("1", ""), field1=0)

    result = parse(Collision, "1", "2")
    assert result == Collision(sub=CollisionSub("1", ""), field1=2)

    result = parse(Collision, "--field2=-1", "1", "2", "3")
    assert result == Collision(sub=CollisionSub("1", "-1"), field1=2, field2=3)
