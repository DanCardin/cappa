from __future__ import annotations

import io
import sys
import typing
from dataclasses import dataclass, field

from rich.console import Console, NewLine
from rich.markdown import Markdown
from rich.markup import escape
from rich.padding import Padding
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from typing_extensions import TypeAlias

prompt_types = (Prompt, Confirm)


Displayable: TypeAlias = typing.Union[str, Text, Table, NewLine, Markdown, Padding]


theme: Theme = Theme(
    {
        "cappa.prog": "grey50",
        "cappa.group": "dark_orange bold",
        "cappa.arg": "cyan",
        "cappa.arg.name": "dark_cyan",
        "cappa.subcommand": "dark_cyan",
        "cappa.help": "default",
    }
)


@dataclass
class Output:
    """Output sink for CLI std out and error streams.

    For simple customization (namely disabling color and overriding the theme),
    `invoke` and `parse` accept `color` and `theme` arguments, which internally
    configure the `output_console` and `error_console` fields.

    For more involved customization, an Output object can be supplied into either `invoke`
    or `parse` functions as well.

    Note, all input arguments to Output are optional.

    Arguments:
        output_console: Output sink, defaults to printing to stdout.
        error_console: Error sink, defaults to printing to stderr.
        output_format: Format string through which output_console output will be
            formatted. The following format string named format arguments can be used
            in `output_format`: prog, code, message.
        error_format: Format string through which output_console error will be
            formatted. The following format string named format arguments can be used
            in `output_format`: prog, code, message.

    Examples:
        >>> output = Output()
        >>> output = Output(error_format="{prog}: error: {message}")
    """

    output_console: Console = field(
        default_factory=lambda: Console(file=sys.stdout, theme=theme)
    )
    error_console: Console = field(
        default_factory=lambda: Console(file=sys.stderr, theme=theme)
    )

    output_format: str = "{message}"
    error_format: str = "[red]Error[/red]: {message}"

    def color(self, value: bool = True):
        """Override the default `color` setting (None), to an explicit True/False value."""
        self.output_console.no_color = not value
        self.error_console.no_color = not value
        return self

    def theme(self, t: Theme | None):
        """Override the default Theme, or reset the theme back to default (with `None`)."""
        self.output_console.push_theme(t or theme)
        self.error_console.push_theme(t or theme)

    def exit(self, e: Exit):
        """Print a `cappa.Exit` object to the appropriate console."""
        if e.code == 0:
            self.output(e)
        else:
            self.error(e)

    def output(
        self, message: list[Displayable] | Displayable | Exit | str | None, **context
    ):
        """Output a message to the `output_console`.

        Additional `**context` can be supplied into the `output_format` string template.
        """
        message = self._format_message(
            self.output_console, message, self.output_format, **context
        )
        self.write(self.output_console, message)

    def error(
        self, message: list[Displayable] | Displayable | Exit | str | None, **context
    ):
        """Output a message to the `error_console`.

        Additional `**context` can be supplied into the `error_format` string template.
        """
        message = self._format_message(
            self.error_console, message, self.error_format, **context
        )
        self.write(self.error_console, message)

    def _format_message(
        self,
        console: Console,
        message: list[Displayable] | Displayable | Exit | str | None,
        format: str,
        **context,
    ) -> Text | str | None:
        code: int | str | None = None
        prog = None
        if isinstance(message, Exit):
            code = message.code
            prog = message.prog
            message = message.message

        if message is None:
            return None

        text = rich_to_ansi(console, message)

        inner_context = {
            "code": code or 0,
            "prog": prog,
            "message": text,
        }
        final_context = {**inner_context, **context}

        return Text.from_markup(format.format(**final_context))

    def write(self, console: Console, message: Text | str | None):
        if message is None:
            return

        console.print(message, overflow="ignore", crop=False)


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
        prog: str | None = None,
    ):
        self.message = message
        self.prog = prog
        super().__init__(code)


class HelpExit(Exit):
    def __init__(
        self,
        message: list[Displayable] | Displayable,
        *,
        code: str | int | None = 0,
        prog: str | None = None,
    ):
        super().__init__(code=code, prog=prog)
        self.message = message


def rich_to_ansi(
    console: Console, message: list[Displayable] | Displayable | str
) -> str:
    with console.capture() as capture:
        if isinstance(message, list):
            for m in message:
                console.print(m)
        else:
            console.print(message)

    return escape(capture.get().strip())
