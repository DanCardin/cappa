from __future__ import annotations

import dataclasses
import re
import typing

if typing.TYPE_CHECKING:
    from cappa.arg import Arg


@dataclasses.dataclass
class ShellHandler:
    name: str
    template: str

    def backend_template(self, prog: str, arg: Arg) -> str:
        try:
            prog, _ = prog.rsplit("/", 1)
        except ValueError:
            pass

        safe_name = re.sub(r"\W*", "", prog.replace("-", "_"), flags=re.ASCII)

        assert isinstance(arg.long, list)
        assert len(arg.long) > 0
        return self.template % {
            "prog_name": prog,
            "safe_prog_name": safe_name,
            "completion_arg": arg.long[0],
        }


@dataclasses.dataclass
class Completion:
    value: str | None = None
    help: str | None = None


@dataclasses.dataclass
class FileCompletion:
    text: str


class CompletionError(RuntimeError):
    def __init__(
        self, *completions: Completion | FileCompletion, value="complete", **_
    ) -> None:
        self.completions = completions
        self.value = value
