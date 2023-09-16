from dataclasses import dataclass
from typing import Annotated

import cappa

from tests.utils import parse


@dataclass
class Sc1:
    ...


@dataclass
class Sc2:
    ...


@dataclass
class Command:
    subcommand: Annotated[Sc1 | Sc2, cappa.Subcommand(types=[Sc1, Sc2])]


def test_required_missing():
    parse(Command, "sc1")
    parse(Command, "sc2")
