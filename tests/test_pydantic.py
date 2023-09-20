from __future__ import annotations

import cappa
from pydantic import BaseModel, dataclasses
from typing_extensions import Annotated

from tests.utils import parse


class PydanticCommand(BaseModel):
    name: str
    foo: Annotated[int, cappa.Arg(short=True)]


def test_base_model():
    result = parse(PydanticCommand, "meow", "-f", "4")
    assert result == PydanticCommand(name="meow", foo=4)


@dataclasses.dataclass
class DataclassCommand:
    name: str
    foo: Annotated[int, cappa.Arg(short=True)]


def test_dataclass():
    result = parse(DataclassCommand, "meow", "-f", "4")
    assert result == DataclassCommand(name="meow", foo=4)
