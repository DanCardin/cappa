from __future__ import annotations

import importlib
from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from cappa.ui.base import serve


@dataclass
class Serve:
    module: Annotated[str, cappa.Arg(help="Given as `module:Class`")]

    @property
    def command_ref(self) -> list[str]:
        return self.module.split(":", 1)


def main():
    command = cappa.parse(Serve)

    module_path, class_name = command.command_ref
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    serve(cls)


if __name__ == "__main__":
    main()
