from __future__ import annotations

import textwrap
from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from cappa.arg import Group
from tests.utils import backends, parse, strip_trailing_whitespace


@backends
def test_implicit_syntax(backend):
    @dataclass
    class ArgTest:
        verbose: Annotated[
            int,
            cappa.Arg(short="-v", action=cappa.ArgAction.count),
            cappa.Arg(long="--verbosity"),
        ] = 0

    result = parse(ArgTest, backend=backend)
    assert result.verbose == 0

    result = parse(ArgTest, "-vv", backend=backend)
    assert result.verbose == 2

    result = parse(ArgTest, "--verbosity", "3", backend=backend)
    assert result.verbose == 3

    with pytest.raises(cappa.Exit) as e:
        parse(ArgTest, "-vv", "--verbosity", "3", backend=backend)
    if backend is None:
        message = "Argument '--verbosity' is not allowed with argument '-v'"
    else:
        message = "argument --verbosity: not allowed with argument -v"

    assert message.lower() == str(e.value.message).lower()


@backends
def test_implicit_syntax_explicit_name(backend, capsys):
    @dataclass
    class ArgTest:
        verbose: Annotated[
            int,
            cappa.Arg(short="-v", action=cappa.ArgAction.count, group="Foo"),
            cappa.Arg(long="--verbosity", group="Foo"),
        ] = 0

    with pytest.raises(cappa.Exit):
        parse(ArgTest, "-h")

    out = capsys.readouterr().out

    expected = textwrap.indent(
        textwrap.dedent(
            """
            Foo
              [-v]                       (Default: 0)
              [--verbosity VERBOSE]      (Default: 0)
            """,
        ),
        "  ",
    )
    assert expected in strip_trailing_whitespace(out)


@backends
def test_explicit_groups(backend):
    @dataclass
    class ArgTest:
        verbose: Annotated[
            int,
            cappa.Arg(
                short="-v",
                action=cappa.ArgAction.count,
                group=Group(name="Verbose", exclusive=True),
            ),
        ] = 0
        verbosity: Annotated[
            int,
            cappa.Arg(long="--verbosity", group=Group(name="Verbose", exclusive=True)),
        ] = 0

    result = parse(ArgTest, backend=backend)
    assert result.verbose == 0
    assert result.verbosity == 0

    result = parse(ArgTest, "-vv", backend=backend)
    assert result.verbose == 2
    assert result.verbosity == 0

    result = parse(ArgTest, "--verbosity", "3", backend=backend)
    assert result.verbose == 0
    assert result.verbosity == 3

    with pytest.raises(cappa.Exit) as e:
        parse(ArgTest, "-vv", "--verbosity", "3", backend=backend)

    if backend is None:
        message = "Argument '--verbosity' is not allowed with argument '-v'"
    else:
        message = "argument --verbosity: not allowed with argument -v"

    assert message.lower() == str(e.value.message).lower()


@backends
def test_differing_group_identity(backend):
    @dataclass
    class ArgTest:
        one: Annotated[int, cappa.Arg(group=Group(name="Verbose", exclusive=False))] = 0
        tw: Annotated[int, cappa.Arg(group=Group(name="Verbose", exclusive=True))] = 0

    with pytest.raises(ValueError) as e:
        parse(ArgTest, backend=backend)

    assert str(e.value) == (
        "Group details between `Group(order=0, name='Verbose', exclusive=False, section=0)` "
        "and `Group(order=0, name='Verbose', exclusive=True, section=0)` must match"
    )
