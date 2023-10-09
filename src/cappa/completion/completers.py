from __future__ import annotations

from cappa.completion.types import Completion


def complete_choices(choices: list[str], help: str | None = None):
    def completion(partial: str = ""):
        return [Completion(c, help=help) for c in choices if partial in c]

    return completion
