from __future__ import annotations

from dataclasses import dataclass
from typing import Union

import cappa
from typing_extensions import Annotated

from tests.utils import parse


@dataclass
class Sc1:
    ...


@dataclass
class Sc2:
    ...


@dataclass
class Command:
    subcommand: Annotated[Union[Sc1, Sc2], cappa.Subcommand(types=[Sc1, Sc2])]


def test_required_missing():
    parse(Command, "sc1")
    parse(Command, "sc2")
