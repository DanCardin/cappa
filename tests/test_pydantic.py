from __future__ import annotations

import sys
from typing import Optional

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends, parse

if sys.version_info < (3, 14):
    from pydantic import BaseModel, Field, dataclasses

    class PydanticCommand(BaseModel):
        name: str
        foo: Annotated[int, cappa.Arg(short=True)]

    @backends
    def test_base_model(backend: Backend):
        result = parse(PydanticCommand, "meow", "-f", "4", backend=backend)
        assert result == PydanticCommand(name="meow", foo=4)

    @dataclasses.dataclass
    class DataclassCommand:
        name: str
        foo: Annotated[int, cappa.Arg(short=True)]

    @backends
    def test_dataclass(backend: Backend):
        result = parse(DataclassCommand, "meow", "-f", "4", backend=backend)
        assert result == DataclassCommand(name="meow", foo=4)

    class OptSub(BaseModel):
        name: Optional[str] = None

    class OptionalSubcommand(BaseModel):
        sub: cappa.Subcommands[Optional[OptSub]] = None

    @backends
    def test_optional_subcommand(backend: Backend):
        result = parse(OptionalSubcommand, backend=backend)
        assert result == OptionalSubcommand(sub=None)

        result = parse(OptionalSubcommand, "opt-sub", backend=backend)
        assert result == OptionalSubcommand(sub=OptSub(name=None))

        result = parse(OptionalSubcommand, "opt-sub", "foo", backend=backend)
        assert result == OptionalSubcommand(sub=OptSub(name="foo"))

    @backends
    def test_class_validation(backend: Backend):
        class Foo(BaseModel):
            bar: Optional[int] = Field(gt=0)

        result = parse(Foo, "3", backend=backend)
        assert result.bar == 3

        with pytest.raises(cappa.Exit) as e:
            parse(Foo, "0", backend=backend)

        assert e.value.code == 2
        assert "greater than 0" in str(e.value.message)
