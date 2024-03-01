from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import Any, List, Optional

from rich.text import Text

from cappa import Arg, Command
from cappa.arg import ArgAction
from cappa.ui.parameter_controls import ValueNotSupplied


@dataclass
class ArgData:
    arg: Arg
    value: Any

    def render(self):
        values = [v for v in self.value if not isinstance(v, ValueNotSupplied)]
        if not values:
            return

        names = self.arg.names()

        if self.arg.action in {ArgAction.store_true, ArgAction.store_false}:
            if values[0]:
                yield names[-1]
        elif names:
            name = names[-1]
            for value in values:
                yield name
                yield value
        else:
            yield from values


@dataclass
class CommandData:
    command: Command
    args_data: list[ArgData]
    parent: Optional[CommandData] = None

    def to_cli_args(self, include_root_command: bool = False) -> List[str]:
        cli_args = self._to_cli_args()
        if not include_root_command:
            cli_args = cli_args[1:]

        return cli_args

    def _to_cli_args(self):
        args = [self.command.real_name()]

        args += [
            segment for arg_data in self.args_data for segment in arg_data.render()
        ]

        return args

    def to_cli_string(self, include_root_command: bool = False) -> Text:
        """Generate a string representing the CLI invocation as if typed directly into the command line.

        Returns:
            A string representing the command invocation.
        """
        args = self.to_cli_args(include_root_command=include_root_command)

        text_renderables = []
        for arg in args:
            if isinstance(arg, ValueNotSupplied):
                value = Text("???", style="bold black on red")
            else:
                value = Text(shlex.quote(str(arg)))

            text_renderables.append(value)

        return Text(" ").join(text_renderables)
