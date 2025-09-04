from __future__ import annotations

from dataclasses import dataclass

import cappa


@dataclass
class DeferImport:
    command: cappa.Subcommands[MeanCommand]


@cappa.command(name="mean", invoke="defer_import.mean.calculate_mean")
@dataclass
class MeanCommand:
    numbers: list[int]


def main():
    cappa.invoke(DeferImport)
