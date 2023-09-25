from dataclasses import dataclass
from typing import List

import cappa
import pytest
from cappa.annotation import parse_list, parse_value

from tests.utils import parse


@dataclass
class Foo:
    bar: str
    baz: List[int]


command = cappa.Command(
    Foo,
    arguments=[
        cappa.Arg(name="bar", parse=str),
        cappa.Arg(name="baz", parse=parse_list(int), num_args=-1),
    ],
    help="Short help.",
    description="Long description.",
)


def test_valid():
    result = parse(command, "one", "2", "3")
    assert result == Foo(bar="one", baz=[2, 3])


def test_help(capsys):
    with pytest.raises(ValueError):
        parse(command, "-h")

    out = capsys.readouterr().out
    assert "Short help." in out
    assert "Long description." in out


def test_subcommand():
    @dataclass
    class Bar:
        bar: str

    @dataclass
    class Foo:
        sub: Bar

    command = cappa.Command(
        Foo,
        arguments=[
            cappa.Subcommands(
                name="sub",
                options={
                    "bar": cappa.Command(
                        Bar,
                        arguments=[
                            cappa.Arg(name="bar", parse=parse_value),
                        ],
                    )
                },
            ),
        ],
        help="Short help.",
        description="Long description.",
    )

    result = parse(command, "bar", "one")
    assert result == Foo(sub=Bar("one"))
