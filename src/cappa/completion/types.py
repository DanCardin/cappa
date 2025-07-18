from __future__ import annotations

import dataclasses
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from cappa.arg import Arg


@dataclasses.dataclass
class ShellHandler:
    name: str
    template: str

    def backend_template(self, prog: str, arg: Arg[Any]) -> str:
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
    arg: Arg[Any] | None = None

    @property
    def description(self) -> str:
        if not self.arg or self.arg.help:
            return self.help or ""

        return f"<{self.arg.value_name}> {self.help}".strip()


@dataclasses.dataclass
class FileCompletion:
    text: str
