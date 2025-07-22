from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable, cast

from cappa.arg import Arg
from cappa.command import Command
from cappa.completion.shells import available_shells
from cappa.output import Exit, Output
from cappa.parser import Completion, FileCompletion, backend


def execute(
    command: Command[Any], prog: str, action: str, arg: Arg[Any], output: Output
):
    shell_name = Path(os.environ.get("SHELL", "bash")).name
    shell = available_shells.get(shell_name)

    if shell is None:
        raise Exit("Unknown shell", code=1)

    if action == "generate":
        raise Exit(shell.backend_template(prog, arg), code=0)

    command_args = parse_incomplete_command()

    backend(
        command,
        command_args,
        output=output,
        prog=prog,
        provide_completions=True,
    )


def parse_incomplete_command() -> list[str]:
    raw_completion_line = os.environ.get("COMPLETION_LINE", "").replace("\n", " ")
    raw_completion_location = os.environ.get("COMPLETION_LOCATION")
    if not raw_completion_line or raw_completion_location is None:
        raise Exit(code=0)

    completion_line = list(split_incomplete_command(raw_completion_line))
    completion_index = int(raw_completion_location)

    return completion_line[1:completion_index]


def split_incomplete_command(string: str) -> Iterable[str]:
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

    result: list[str] = []
    for item in completions:
        item = cast(Completion, item)
        result.append(f"{item.value}:{item.description}")
    return "\n".join(result)
