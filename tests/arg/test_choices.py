from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends, parse


@backends
def test_manually_specified_choices(backend: Backend):
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
def test_optional_set_of_choices(backend: Backend, capsys: Any):
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
def test_variadic_tuple_choices(backend: Backend, capsys: Any):
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
def test_tuple_choices(backend: Backend, capsys: Any):
    @dataclass
    class ArgTest:
        choice: Annotated[
            tuple[Literal["one", "two"], int] | None, cappa.Arg(short=True)
        ] = None

    with pytest.raises(cappa.HelpExit):
        parse(ArgTest, "--help", backend=backend)

    result = capsys.readouterr().out
    assert "Valid options: one, two." not in result


@backends
def test_literal_parse_sequence(backend: Backend):
    @dataclass
    class LiteralParse:
        log_level: Annotated[
            str,
            cappa.Arg(
                short="-L", long=True, choices=["DEBUG"], parse=[str.upper, str.strip]
            ),
        ] = "DEBUG"

    result = parse(LiteralParse, "--log-level", "  debug  ", backend=backend)
    assert result == LiteralParse(log_level="DEBUG")


explicit_choice_default = ["1s", "1m"]


@backends
def test_explicit_choice_sequence(backend: Backend):
    @dataclass
    class Example:
        interval: Annotated[
            list[str] | None, cappa.Arg(choices=explicit_choice_default, default=["1m"])
        ]

    result = parse(Example, backend=backend)
    assert result == Example(interval=["1m"])

    result = parse(Example, "1s", backend=backend)
    assert result == Example(interval=["1s"])

    with pytest.raises(cappa.Exit) as e:
        parse(Example, "2s", backend=backend)

    assert (
        e.value.message
        == "Invalid value for 'interval': Invalid choice: '2s' (choose from '1s', '1m')"
    )
