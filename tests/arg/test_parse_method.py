from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@dataclass
class Config:
    path: str

    @classmethod
    def from_classmethod(cls, path: str):
        return cls(path)

    def from_method(self, path: str) -> str:
        return "/".join([self.path, path])


config = Config("foo")


@backends
def test_from_classmethod(backend):
    @cappa.command(name="command")
    @dataclass
    class Command:
        config: Annotated[Config, cappa.Arg(parse=Config.from_classmethod)]

    test = parse(Command, "foo", backend=backend)
    assert test == Command(config=Config("foo"))


@backends
def test_method(backend):
    @cappa.command(name="command")
    @dataclass
    class Command:
        config: Annotated[str, cappa.Arg(parse=config.from_method)]

    test = parse(Command, "bar", backend=backend)
    assert test == Command(config="foo/bar")
