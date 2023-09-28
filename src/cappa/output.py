from __future__ import annotations

import sys
import typing

from cappa.rich import print as rich_print


class Exit(SystemExit):
    def __init__(self, message: str | None = None, *, code: str | int | None = 0):
        self.message = message
        super().__init__(code)

    def print(self):
        if self.message:
            print(self.message, flush=True)


def print(message: str, rich: typing.Any = rich_print, flush=False):
    if rich and rich_print:
        rich_print(message, file=sys.stderr, flush=flush)
    else:
        sys.stderr.write(message + "\n")
        if flush:
            sys.stderr.flush()


__all__ = [
    "Exit",
    "print",
]
