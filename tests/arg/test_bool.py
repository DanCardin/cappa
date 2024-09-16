from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@backends
def test_missing_default(backend):
    @dataclass
    class ArgTest:
        default: bool

    test = parse(ArgTest, backend=backend)
    assert test.default is False

    test = parse(ArgTest, "--default", backend=backend)
    assert test.default is True


@backends
def test_default(backend):
    @dataclass
    class ArgTest:
        default: bool = False

    test = parse(ArgTest, backend=backend)
    assert test.default is False

    test = parse(ArgTest, "--default", backend=backend)
    assert test.default is True


@backends
def test_explicit_short(backend):
    @dataclass
    class ArgTest:
        explicit_short: Annotated[bool, cappa.Arg(short="-e")] = False

    test = parse(ArgTest, backend=backend)
    assert test.explicit_short is False

    test = parse(ArgTest, "-e", backend=backend)
    assert test.explicit_short is True


@backends
def test_explicit_long(backend):
    @dataclass
    class ArgTest:
        explicit_long: Annotated[bool, cappa.Arg(long="--meow")] = False

    test = parse(ArgTest, backend=backend)
    assert test.explicit_long is False

    test = parse(ArgTest, "--meow", backend=backend)
    assert test.explicit_long is True


@backends
def test_store_false(backend):
    @dataclass
    class ArgTest:
        default_true: Annotated[bool, cappa.Arg(long="--false")] = True

    test = parse(ArgTest, backend=backend)
    assert test.default_true is True

    test = parse(ArgTest, "--false", backend=backend)
    assert test.default_true is False


@backends
def test_true_false_option(backend):
    @dataclass
    class ArgTest:
        true_false: Annotated[bool, cappa.Arg(long="--true/--no-true")] = True

    test = parse(ArgTest, backend=backend)
    assert test.true_false is True

    test = parse(ArgTest, "--true", backend=backend)
    assert test.true_false is True

    test = parse(ArgTest, "--no-true", backend=backend)
    assert test.true_false is False

    with pytest.raises(cappa.Exit) as e:
        parse(ArgTest, "--garbage", backend=backend)

    assert e.value.code == 2
    assert "unrecognized arguments: --garbage" in str(e.value.message).lower()


@backends
def test_optional_bool(backend):
    """Optional bool with default should still infer store_true/false action."""

    @dataclass
    class ArgTest:
        true_false: Annotated[bool | None, cappa.Arg(long="--true/--no-true")] = None

    test = parse(ArgTest, backend=backend)
    assert test.true_false is None

    test = parse(ArgTest, "--true", backend=backend)
    assert test.true_false is True

    test = parse(ArgTest, "--no-true", backend=backend)
    assert test.true_false is False


@backends
def test_optional_bool_no_default(backend):
    """Optional bool should default to None rather than bool."""

    @dataclass
    class ArgTest:
        true_false: Annotated[bool | None, cappa.Arg(long="--true/--no-true")]

    test = parse(ArgTest, backend=backend)
    assert test.true_false is None


@backends
def test_optional_bool_and_int(backend):
    """Union of multiple types, including bool does not infer bool action."""

    @dataclass
    class ArgTest:
        true_false: Annotated[bool | int | None, cappa.Arg(short=True)]

    test = parse(ArgTest, backend=backend)
    assert test.true_false is None

    test = parse(ArgTest, "-t", "4", backend=backend)
    assert test.true_false == 4

    test = parse(ArgTest, "-t", "asdf", backend=backend)
    assert test.true_false is True


@backends
def test_env_default_value_precedence(backend):
    """Assert a bool flag yields correct value given an env default."""

    @dataclass
    class ArgTest:
        env_default: Annotated[
            bool, cappa.Arg(long=True, default=cappa.Env("ENV_DEFAULT"))
        ] = False

    test = parse(ArgTest, backend=backend)
    assert test.env_default is False

    with patch("os.environ", new={"ENV_DEFAULT": "1"}):
        test = parse(ArgTest, backend=backend)
    assert test.env_default is True

    test = parse(ArgTest, "--env-default", backend=backend)
    assert test.env_default is True

    with patch("os.environ", new={"ENV_DEFAULT": "1"}):
        test = parse(ArgTest, "--env-default", backend=backend)
    assert test.env_default is True


@backends
def test_sole_no_arg(backend):
    @dataclass
    class ArgTest:
        no_dry_run: bool = False

    test = parse(ArgTest, backend=backend)
    assert test.no_dry_run is False

    test = parse(ArgTest, "--no-dry-run", backend=backend)
    assert test.no_dry_run is True


@backends
def test_sole_no_arg_inverted(backend):
    @dataclass
    class ArgTest:
        no_dry_run: bool = True

    test = parse(ArgTest, backend=backend)
    assert test.no_dry_run is True

    test = parse(ArgTest, "--no-dry-run", backend=backend)
    assert test.no_dry_run is False
