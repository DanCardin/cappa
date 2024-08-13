from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pytest

import cappa
from cappa.output import Exit
from cappa.parse import parse_list, parse_value
from tests.utils import backends, parse


@dataclass
class Foo:
    bar: str
    baz: list[int]


command = cappa.Command(
    Foo,
    arguments=[
        cappa.Arg(field_name="bar"),
        cappa.Arg(field_name="baz", parse=parse_list(List[int]), num_args=-1),
    ],
    help="Short help.",
    description="Long description.",
)


@backends
def test_valid(backend):
    result = parse(command, "one", "2", "3", backend=backend)
    assert result == Foo(bar="one", baz=[2, 3])


@pytest.mark.help
@backends
def test_help(capsys, backend):
    with pytest.raises(Exit):
        parse(command, "-h", backend=backend)

    out = capsys.readouterr().out
    assert "Short help." in out
    assert "Long description." in out


@dataclass
class Bar:
    bar: str


@dataclass
class Foo2:
    sub: Bar


@backends
def test_subcommand(backend):
    command = cappa.Command(
        Foo2,
        arguments=[
            cappa.Subcommand(
                field_name="sub",
                options={
                    "bar": cappa.Command(
                        Bar,
                        arguments=[
                            cappa.Arg(field_name="bar", parse=parse_value(str)),
                        ],
                    )
                },
            ),
        ],
        help="Short help.",
        description="Long description.",
    )

    result = parse(command, "bar", "one", backend=backend)
    assert result == Foo2(sub=Bar("one"))
