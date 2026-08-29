from __future__ import annotations

from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends, invoke, parse


@cappa.command(name="ping")
def ping() -> str:
    return "pong"


@dataclass
class Add:
    value: int


@dataclass
class Sub:
    value: int


@cappa.command(subcommands=[ping])
@dataclass
class Mixed:
    sub: cappa.Subcommands[Add | Sub | None] = None


@cappa.command(subcommands=[ping])
@dataclass
class ExplicitFieldName:
    sub: Annotated[Add | Sub | None, cappa.Subcommand(field_name="sub")] = None


@dataclass
class TwoSources:
    one: cappa.Subcommands[Add | Sub]
    two: cappa.Subcommands[Add | Sub]


@backends
def test_mixed_value_subcommand(backend: Backend):
    result = parse(Mixed, "add", "1", backend=backend)
    assert result == Mixed(sub=Add(value=1))


@backends
def test_mixed_valueless_subcommand(backend: Backend):
    assert invoke(Mixed, "ping", backend=backend) == "pong"


@backends
def test_explicit_field_name(backend: Backend):
    result = parse(ExplicitFieldName, "sub", "1", backend=backend)
    assert result == ExplicitFieldName(sub=Sub(value=1))


@backends
def test_multiple_attribute_sources(backend: Backend):
    with pytest.raises(ValueError, match="Only one subcommand"):
        invoke(TwoSources, "add", "1", backend=backend)
