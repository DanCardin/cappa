import sys
import typing

try:
    import rich as _rich
except ImportError:  # pragma: no cover
    _rich = None


class Exit(SystemExit):
    def __init__(self, message: str | None = None, *, code: str | int | None = 0):
        self.message = message
        super().__init__(code)

    def print(self):
        if self.message:
            print(self.message, flush=True)


def print(message: str, rich: typing.Any = _rich, flush=False):
    if rich and _rich:
        _rich.print(message, file=sys.stderr, flush=flush)
    else:
        sys.stderr.write(message + "\n")
        if flush:
            sys.stderr.flush()


__all__ = [
    "Exit",
    "print",
]
