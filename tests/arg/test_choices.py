from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@backends
def test_manually_specified_choices(backend):
    @dataclass
    class ArgTest:
        choice: Annotated[str, cappa.Arg(choices=["a", "1"])]

    result = parse(ArgTest, "a")
    assert result.choice == "a"

    result = parse(ArgTest, "1")
    assert result.choice == "1"

    with pytest.raises(cappa.Exit) as e:
        parse(ArgTest, "two", backend=backend)

    message = str(e.value.message).lower()
    assert "invalid choice: 'two' (choose from 'a', '1')" in message


@backends
def test_optional_set_of_choices(backend, capsys):
    @dataclass
    class ArgTest:
        choice: Annotated[set[Literal["one", "two"]] | None, cappa.Arg(short=True)] = (
            None
        )

    with pytest.raises(cappa.HelpExit):
        parse(ArgTest, "--help", backend=backend)

    result = capsys.readouterr().out
    assert "Valid options: one, two." in result


@backends
def test_variadic_tuple_choices(backend, capsys):
    @dataclass
    class ArgTest:
        choice: Annotated[
            tuple[Literal["one", "two"], ...] | None, cappa.Arg(short=True)
        ] = None

    with pytest.raises(cappa.HelpExit):
        parse(ArgTest, "--help", backend=backend)

    result = capsys.readouterr().out
    assert "Valid options: one, two." in result


@backends
def test_tuple_choices(backend, capsys):
    @dataclass
    class ArgTest:
        choice: Annotated[
            tuple[Literal["one", "two"], int] | None, cappa.Arg(short=True)
        ] = None

    with pytest.raises(cappa.HelpExit):
        parse(ArgTest, "--help", backend=backend)

    result = capsys.readouterr().out
    assert "Valid options: one, two." not in result
