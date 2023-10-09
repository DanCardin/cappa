from __future__ import annotations

import cappa
from pydantic import BaseModel, dataclasses
from typing_extensions import Annotated

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
