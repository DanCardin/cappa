from __future__ import annotations

import io
import sys
import typing
from dataclasses import dataclass

from rich.console import Console, NewLine
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from typing_extensions import TypeAlias

prompt_types = (Prompt, Confirm)


Displayable: TypeAlias = typing.Union[str, Text, Table, NewLine]


@dataclass
class Output:
    output_console: Console
    error_console: Console
    theme: typing.ClassVar[Theme] = Theme(
        {
            "cappa.prog": "grey50",
            "cappa.group": "dark_orange bold",
            "cappa.arg": "cyan",
            "cappa.arg.name": "dark_cyan",
            "cappa.subcommand": "dark_cyan",
            "cappa.help": "default",
        }
    )

    @classmethod
    def from_theme(cls, theme: Theme | None = None):
        output_console = Console(file=sys.stdout, theme=theme or cls.theme)
        error_console = Console(file=sys.stderr, theme=theme or cls.theme)
        return cls(output_console, error_console)

    def exit(self, e: Exit):
        if e.code == 0:
            self.output(e)
        else:
            self.error(e)

    def output(self, message: list[Displayable] | Displayable | Exit | None):
        self.write(self.output_console, message)

    def error(self, message: list[Displayable] | Displayable | Exit | None):
        self.write(self.error_console, message)

    def write(
        self, console: Console, message: list[Displayable] | Displayable | Exit | None
    ):
        if isinstance(message, Exit):
            message = message.message

        if message is None:
            return

        if isinstance(message, list):
            messages = message
        else:
            messages = [message]

        for m in messages:
            console.print(m)


class TestPrompt(Prompt):
    def __init__(self, prompt, *, input, default=..., **kwargs):
        self.file = io.StringIO()
        self.default = default
        self.stream = io.StringIO(input)

        console = Console(file=self.file)
        super().__init__(prompt=prompt, console=console, **kwargs)

    def __call__(self):
        return super().__call__(default=self.default, stream=self.stream)


class Exit(SystemExit):
    def __init__(
        self,
        message: list[Displayable] | Displayable | None = None,
        *,
        code: str | int | None = 0,
    ):
        self.message = message
        super().__init__(code)


class HelpExit(Exit):
    def __init__(
        self,
        message: list[Displayable] | Displayable,
        *,
        code: str | int | None = 0,
    ):
        super().__init__(code=code)
        self.message = message
