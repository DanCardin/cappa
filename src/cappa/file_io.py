from __future__ import annotations

import sys
from dataclasses import dataclass

import cappa


@dataclass
class FileMode:
    """Factory for creating file object types.

    Instances of FileType are typically passed as type= arguments to the
    ArgumentParser add_argument() method.

    Arguments:
        mode: The file mode to use to open the file. Passes directly through to builtin `open()`.
        buffering: The file's desired buffer size. Passes directly through to builtin `open()`.
        encoding: The file's encoding. Passes directly through to builtin `open()`.
        errors: A string indicating how encoding and decoding errors are to
            be handled. Passes directly through to builtin `open()`.

        error_code: The exit code to use when an error occurs. Defaults to 1. Note this is **not**
            an `open()` argument.
    """

    mode: str = "r"
    buffering: int = -1
    encoding: str | None = None
    errors: str | None = None

    error_code: int = 1

    def __call__(self, filename: str):
        """Open the given `filename` and return the file handle.

        Supply "-" as the filename to read from stdin or write to stdout,
        depending on the chosen `mode`.
        """
        # the special argument "-" means sys.std{in,out}
        if filename == "-":
            if "r" in self.mode:
                if "b" in self.mode:
                    return sys.stdin.buffer
                return sys.stdin

            if any(c for c in self.mode if c in {"w", "a", "x"}):
                if "b" in self.mode:
                    return sys.stdout.buffer
                return sys.stdout

            raise cappa.Exit(
                f"Invalid mode '{self.mode}' with supplied '-' file name.",
                code=self.error_code,
            )

        try:
            return open(filename, self.mode, self.buffering, self.encoding, self.errors)
        except OSError as e:
            raise cappa.Exit(f"Cannot open {filename}: {e}", code=self.error_code)
