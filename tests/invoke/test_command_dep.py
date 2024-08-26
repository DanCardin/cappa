from __future__ import annotations

from dataclasses import dataclass
from typing import Union

import cappa
from tests.utils import backends, invoke


@dataclass
class Subcommand:
    ...

    def __call__(self, command: cappa.Command):
        return command.real_name()


@dataclass
class TopLevelCommand:
    subcmd: cappa.Subcommands[Union[Subcommand, None]] = None

    def __call__(self, command: cappa.Command):
        return command.real_name()


@backends
def test_command_as_dependency(backend):
    result = invoke(TopLevelCommand, backend=backend)
    assert result == "top-level-command"

    result = invoke(TopLevelCommand, "subcommand", backend=backend)
    assert result == "subcommand"
