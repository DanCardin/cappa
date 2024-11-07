from __future__ import annotations

import re
from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@dataclass
class Foo: ...


@dataclass
class Args:
    subcommand: Annotated[Foo, cappa.Subcommand(group="Yup")]


@backends
def test_required_missing(backend, capsys):
    with pytest.raises(cappa.Exit) as e:
        parse(Args, "--help", backend=backend)
    assert e.value.code == 0

    help = capsys.readouterr().out
    assert re.match(r".*Yup:?[\n\s]+\{?foo.*", help, re.DOTALL)


@backends
def test_explicit_group(backend, capsys):
    @dataclass
    class Args:
        subcommand: Annotated[Foo, cappa.Subcommand(group=cappa.Group(name="Yup"))]

    with pytest.raises(cappa.Exit) as e:
        parse(Args, "--help", backend=backend)
    assert e.value.code == 0

    help = capsys.readouterr().out
    assert re.match(r".*Yup:?[\n\s]+\{?foo.*", help, re.DOTALL)


@backends
def test_tuple_group(backend, capsys):
    @dataclass
    class Args:
        subcommand: Annotated[Foo, cappa.Subcommand(group=(1, "Yup"))]

    with pytest.raises(cappa.Exit) as e:
        parse(Args, "--help", backend=backend)
    assert e.value.code == 0

    help = capsys.readouterr().out
    assert re.match(r".*Yup:?[\n\s]+\{?foo.*", help, re.DOTALL)
