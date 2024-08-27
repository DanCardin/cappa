from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, dataclasses
from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


class PydanticCommand(BaseModel):
    name: str
    foo: Annotated[int, cappa.Arg(short=True)]


@backends
def test_base_model(backend):
    result = parse(PydanticCommand, "meow", "-f", "4", backend=backend)
    assert result == PydanticCommand(name="meow", foo=4)


@dataclasses.dataclass
class DataclassCommand:
    name: str
    foo: Annotated[int, cappa.Arg(short=True)]


@backends
def test_dataclass(backend):
    result = parse(DataclassCommand, "meow", "-f", "4", backend=backend)
    assert result == DataclassCommand(name="meow", foo=4)


class OptSub(BaseModel):
    name: Optional[str] = None


class OptionalSubcommand(BaseModel):
    sub: cappa.Subcommands[Optional[OptSub]] = None


@backends
def test_optional_subcommand(backend):
    result = parse(OptionalSubcommand, backend=backend)
    assert result == OptionalSubcommand(sub=None)

    result = parse(OptionalSubcommand, "opt-sub", backend=backend)
    assert result == OptionalSubcommand(sub=OptSub(name=None))

    result = parse(OptionalSubcommand, "opt-sub", "foo", backend=backend)
    assert result == OptionalSubcommand(sub=OptSub(name="foo"))
