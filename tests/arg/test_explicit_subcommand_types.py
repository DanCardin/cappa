from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@dataclass
class Sc1: ...


@dataclass
class Sc2: ...


@dataclass
class Command:
    subcommand: Annotated[Union[Sc1, Sc2], cappa.Subcommand(types=[Sc1, Sc2])]


@backends
def test_required_missing(backend):
    parse(Command, "sc1", backend=backend)
    parse(Command, "sc2", backend=backend)
