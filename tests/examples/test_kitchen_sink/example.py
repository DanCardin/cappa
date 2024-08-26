#!/usr/bin/env python

from __future__ import annotations

import enum
import logging
import sqlite3
from dataclasses import dataclass, field
from typing import Literal, Union

from typing_extensions import Annotated

import cappa

log = logging.getLogger(__name__)


class OtherOptions(enum.Enum):
    a = "a"
    b = "b"
    c = "c"


@dataclass
class Example:
    """Example program.

    Args:
       name: Required name argument
       flag: optional flag to enable
    """

    name: str
    value: Annotated[int, cappa.Arg(short="-V", long="--val", default=0)]

    options: Annotated[
        Union[Literal["one"], Literal["two"], Literal[3]], cappa.Arg(short=True)
    ]
    moptions: Annotated[OtherOptions, cappa.Arg(short=True)]

    subcommand: Annotated[Union[MeowCommand, BarkCommand], cappa.Subcommand]

    flags: Annotated[list[str], cappa.Arg(short=True, long=True)] = field(
        default_factory=list
    )
    flag: bool = False  # --flag


def db() -> sqlite3.Connection:
    return sqlite3.connect("sqlite:///")


def meow(
    command: Example,
    meow: MeowCommand,
    db: Annotated[sqlite3.Connection, cappa.Dep(db)],
):
    result = db.execute(f"select '{command.name}', {meow.times} + 1").fetchone()
    log.info(result)


@cappa.command(name="meow", invoke=meow)
@dataclass
class MeowCommand:
    times: int


def bark(bark: BarkCommand):
    log.info(bark)


@cappa.command(name="bark", invoke=bark)
@dataclass
class BarkCommand: ...


# invoke cli parsing
def main(argv=None):
    logging.basicConfig()

    args: Example = cappa.parse(Example, argv=argv, version="1.2.3")
    log.info(args)

    cappa.invoke(Example, argv=argv, version="1.2.3")


if __name__ == "__main__":
    main()
