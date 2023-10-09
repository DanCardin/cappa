from __future__ import annotations

import os
import typing
from pathlib import Path

from cappa.arg import Arg
from cappa.command import Command
from cappa.completion.shells import available_shells
from cappa.output import Exit
from cappa.parser import Completion, FileCompletion, backend


def execute(
    command: Command,
    prog: str,
    action: str,
    help: Arg | None,
    version: Arg | None,
    completion: Arg,
):
    shell_name = Path(os.environ.get("SHELL", "bash")).name
    shell = available_shells.get(shell_name)

    if shell is None:
        raise Exit("Unknown shell", code=1)

    if action == "generate":
        raise Exit(shell.backend_template(prog, completion), code=0)

    command_args = parse_incomplete_command()

    backend(
        command,
        [prog, *command_args],
        version=version,
        help=help,
        provide_completions=True,
    )


def parse_incomplete_command() -> list[str]:
    raw_completion_line = os.environ.get("COMPLETION_LINE", "").replace("\n", " ")
    raw_completion_location = os.environ.get("COMPLETION_LOCATION")
    if raw_completion_line is None or raw_completion_location is None:
        raise Exit(code=0)

    completion_line = list(split_incomplete_command(raw_completion_line))
    completion_index = int(raw_completion_location)

    return completion_line[1:completion_index]


def split_incomplete_command(string: str) -> typing.Iterable[str]:
    import shlex

    lex = shlex.shlex(string, posix=True)
    lex.whitespace_split = True
    lex.commenters = ""

    try:
        yield from lex
    except ValueError:
        yield lex.token


def format_completions(*completions: Completion | FileCompletion) -> str | None:
    if not completions:
        return None

    if isinstance(completions[0], FileCompletion):
        return "file"

    result = []
    for item in completions:
        item = typing.cast(Completion, item)
        result.append(f"{item.value}:{item.help if item.help else ''}")
    return "\n".join(result)
