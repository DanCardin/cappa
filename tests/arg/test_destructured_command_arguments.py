from __future__ import annotations

from dataclasses import dataclass

from type_lens import TypeView
from typing_extensions import Annotated

import cappa
from cappa.default import Default
from cappa.destructure import Destructure
from cappa.registry import default_registry
from tests.utils import parse


@dataclass
class Config:
    color: Annotated[str, cappa.Arg(long=True)]


@dataclass
class Args:
    config: Config


def test_prebuilt_destructure_in_command_arguments():
    destructure = Destructure.collect(
        "config",
        Default(),
        True,
        TypeView(Config),
        registry=default_registry,
    )
    assert destructure is not None

    command = cappa.Command(Args, arguments=destructure.explode_args())
    test = parse(command, "--color=red")
    assert test == Args(config=Config(color="red"))
