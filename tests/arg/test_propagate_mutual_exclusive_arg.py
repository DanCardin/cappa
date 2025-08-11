from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import parse


@dataclass
class Args:
    foo: Annotated[
        bool,
        cappa.Arg(
            long=["--foo", "--no-foo"],
            propagate=True,
            default=False,
            help="Enable or disable foo feature",
        ),
    ]
    subcommand: cappa.Subcommands[Sub]


@dataclass
class Sub:
    name: str


def test_propagated_arg():
    result = parse(Args, "--foo", "sub", "bar")
    assert result == Args(foo=True, subcommand=Sub(name="bar"))

    result = parse(Args, "--no-foo", "sub", "bar")
    assert result == Args(foo=False, subcommand=Sub(name="bar"))

    result = parse(Args, "sub", "--foo", "bar")
    assert result == Args(foo=True, subcommand=Sub(name="bar"))

    result = parse(Args, "sub", "--no-foo", "bar")
    assert result == Args(foo=False, subcommand=Sub(name="bar"))
