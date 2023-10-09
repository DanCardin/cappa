from __future__ import annotations

from dataclasses import dataclass

import cappa
import pytest
from typing_extensions import Annotated

from tests.utils import backends, parse


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
