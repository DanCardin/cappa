from dataclasses import dataclass

import cappa
from tests.utils import backends, invoke


@dataclass
class SubSubCommand:
    """Sub-subcommand."""

    def __call__(self) -> int:
        return 4


@dataclass
class SubCommand:
    subcommand: cappa.Subcommands[SubSubCommand]


@dataclass
class MainCommand:
    subcommand: cappa.Subcommands[SubCommand]


@backends
def test_parent_commands_dont_require_invoke_fn(backend):
    result = invoke(MainCommand, "sub-command", "sub-sub-command", backend=backend)
    assert result == 4
