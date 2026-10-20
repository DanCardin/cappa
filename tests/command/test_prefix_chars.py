from __future__ import annotations

from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from cappa.arg import is_long_name
from tests.utils import CapsysOutput, parse


@cappa.command(prefix_chars="/")
@dataclass
class Windows:
    foo: Annotated[int, cappa.Arg(short=True, long=True)] = 0
    verbose: Annotated[bool, cappa.Arg(short=["/v", "/verbose"])] = False
    path: str = "x"


def test_is_long_name():
    assert is_long_name("--foo")
    assert is_long_name("//foo", "/")
    assert is_long_name("/-foo", "-/")
    assert not is_long_name("-f")
    assert not is_long_name("/foo", "-/")
    assert not is_long_name("-", "-")


def test_inferred_names_use_first_prefix_char():
    assert parse(Windows, "/f", "4") == Windows(foo=4)
    assert parse(Windows, "//foo", "5") == Windows(foo=5)
    assert parse(Windows, "//foo=6") == Windows(foo=6)


def test_dash_is_a_value_when_not_a_prefix():
    assert parse(Windows, "/f", "-4") == Windows(foo=-4)
    assert parse(Windows, "-x") == Windows(path="-x")


def test_dash_dash_still_terminates():
    assert parse(Windows, "--", "/f") == Windows(path="/f")


def test_single_prefix_exact_match_not_split():
    # `/verbose` must not be split into `/v` + `erbose`.
    assert parse(Windows, "/verbose") == Windows(verbose=True)
    assert parse(Windows, "/v") == Windows(verbose=True)


def test_concatenated_short_options():
    @cappa.command(prefix_chars="+-")
    @dataclass
    class Cmd:
        a: Annotated[bool, cappa.Arg(short=True)] = False
        b: Annotated[bool, cappa.Arg(short=True)] = False
        c: Annotated[int, cappa.Arg(short=True)] = 0

    assert parse(Cmd, "+ab") == Cmd(a=True, b=True)
    assert parse(Cmd, "+abc4") == Cmd(a=True, b=True, c=4)
    assert parse(Cmd, "+c", "3") == Cmd(c=3)


def test_multiple_prefixes_infer_with_first():
    @cappa.command(prefix_chars="-/")
    @dataclass
    class Cmd:
        foo: Annotated[int, cappa.Arg(short=True, long=True)] = 0
        other: Annotated[int, cappa.Arg(short="/o")] = 0

    assert parse(Cmd, "-f", "1") == Cmd(foo=1)
    assert parse(Cmd, "--foo", "2") == Cmd(foo=2)
    assert parse(Cmd, "/o", "3") == Cmd(other=3)


def test_unknown_prefix_is_error(capsys: pytest.CaptureFixture[str]):
    with pytest.raises(cappa.Exit):
        parse(Windows, "/z")
    assert "Unrecognized arguments: /z" in CapsysOutput.from_capsys(capsys).stderr


def test_builtin_help_uses_prefix():
    with pytest.raises(cappa.HelpExit):
        parse(Windows, "/h")

    with pytest.raises(cappa.HelpExit):
        parse(Windows, "//help")


def test_negated_bool():
    @cappa.command(prefix_chars="/", default_negate_bool=True)
    @dataclass
    class Cmd:
        flag: Annotated[bool, cappa.Arg(long=True)] = True

    assert parse(Cmd, "//no-flag") == Cmd(flag=False)
    assert parse(Cmd, "//flag") == Cmd(flag=True)


def test_empty_prefix_chars():
    @cappa.command(prefix_chars="")
    @dataclass
    class Cmd: ...

    with pytest.raises(ValueError, match="prefix_chars"):
        parse(Cmd)


@dataclass
class Inner:
    foo: Annotated[int, cappa.Arg(long=True)] = 0


@cappa.command(prefix_chars="/")
@dataclass
class Outer:
    inner: cappa.Destructured[Inner]


def test_destructured_uses_outer_prefix():
    assert parse(Outer, "//foo", "3") == Outer(inner=Inner(foo=3))


@cappa.command(prefix_chars="/")
@dataclass
class Sub:
    foo: Annotated[int, cappa.Arg(long=True)] = 0


@dataclass
class Parent:
    sub: cappa.Subcommands[Sub]
    bar: Annotated[int, cappa.Arg(long=True)] = 0


def test_subcommand_has_own_prefix_chars():
    assert parse(Parent, "--bar", "1", "sub", "//foo", "2") == Parent(
        sub=Sub(foo=2), bar=1
    )


def test_slash_delimited_names_disabled_when_slash_is_prefix():
    @cappa.command(prefix_chars="/")
    @dataclass
    class Cmd:
        foo: Annotated[int, cappa.Arg(short="/f/g")] = 0

    # Treated as the single name `/f/g`, rather than `/f` and `/g`.
    assert parse(Cmd, "/f/g", "1") == Cmd(foo=1)


def test_argparse_backend():
    assert parse(Windows, "/f", "4", backend=cappa.argparse.backend) == Windows(foo=4)
    assert parse(Windows, "//foo=5", backend=cappa.argparse.backend) == Windows(foo=5)
    assert parse(Windows, "/verbose", backend=cappa.argparse.backend) == Windows(
        verbose=True
    )
