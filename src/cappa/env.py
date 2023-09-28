from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Env:
    """Lazily evaluates environment variables in the order given.

    Argument value interpolation will handle and `Arg`'s default being an `Env`
    instance, by evaluating the `Env`, in the event the parser-level value
    fell back to the default.

    Examples:
        >>> from cappa import Arg, Env
        >>> arg = Arg(default=Env("HOST", "HOSTNAME", default="localhost"))
    """

    env_vars: tuple[str, ...]
    default: str | None

    def __init__(self, env_var: str, *env_vars: str, default: str | None = None):
        self.env_vars = (env_var, *env_vars)
        self.default = default

    def evaluate(self) -> str | None:
        for env_var in self.env_vars:
            value = os.getenv(env_var)
            if value:
                return value

        return self.default
