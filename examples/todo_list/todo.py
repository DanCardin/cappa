from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import cappa


@dataclass
class Todo:
    command: cappa.Subcommands[AddCommand | ListCommand]


@cappa.command(name="add")
@dataclass
class AddCommand:
    todo: str

    def __call__(self):
        path = Path("todo.json")

        data = []
        if path.exists():
            data = json.loads(path.read_text())

        data.append(self.todo)
        path.write_text(json.dumps(data))


@cappa.command(name="list")
@dataclass
class ListCommand:
    def __call__(self, output: cappa.Output):
        path = Path("todo.json")

        data = []
        if path.exists():
            data = json.loads(path.read_text())

        for item in data:
            output.output(f" - {item}")


cappa.invoke(Todo)
