from dataclasses import dataclass
from typing import List

import cappa
import pytest
from cappa.annotation import parse_list, parse_value
from cappa.output import Exit

from tests.utils import backends, parse


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


@backends
def test_subcommand(backend):
    @dataclass
    class Bar:
        bar: str

    @dataclass
    class Foo:
        sub: Bar

    command = cappa.Command(
        Foo,
        arguments=[
            cappa.Subcommand(
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

    result = parse(command, "bar", "one", backend=backend)
    assert result == Foo(sub=Bar("one"))
