from __future__ import annotations

import enum
from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import parse


class Flavor(enum.Enum):
    vanilla = "vanilla"
    chocolate = "chocolate"


@dataclass
class Attributes:
    color: Annotated[str, cappa.Arg(long="attribute.color")]
    flavors: Annotated[list[Flavor], cappa.Arg(value_name="attribute.flavor")]
    something: Annotated[int, cappa.Arg(short="-p")]
    custom_parse: Annotated[str, cappa.Arg(long="foo", parse=lambda _: "always this")]  # pyright: ignore
    custom_action: Annotated[int, cappa.Arg(long="bar", action=lambda: 42)]  # pyright: ignore
    optional: Annotated[int, cappa.Arg(long="baz")] = 4


@dataclass
class Args:
    attrs: Annotated[cappa.Destructured[Attributes], cappa.Arg(hidden=True)]


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
