from __future__ import annotations

from dataclasses import dataclass

import cappa
import pytest
from typing_extensions import Annotated

from tests.utils import parse


def test_default():
    @dataclass
    class ArgTest:
        default: bool = False

    test = parse(ArgTest)
    assert test.default is False

    test = parse(ArgTest, "--default")
    assert test.default is True


def test_explicit_short():
    @dataclass
    class ArgTest:
        explicit_short: Annotated[bool, cappa.Arg(short="-es")] = False

    test = parse(ArgTest)
    assert test.explicit_short is False

    test = parse(ArgTest, "-es")
    assert test.explicit_short is True


def test_explicit_long():
    @dataclass
    class ArgTest:
        explicit_long: Annotated[bool, cappa.Arg(long="--meow")] = False

    test = parse(ArgTest)
    assert test.explicit_long is False

    test = parse(ArgTest, "--meow")
    assert test.explicit_long is True


def test_store_false():
    @dataclass
    class ArgTest:
        default_true: Annotated[bool, cappa.Arg(long="--false")] = True

    test = parse(ArgTest)
    assert test.default_true is True

    test = parse(ArgTest, "--false")
    assert test.default_true is False


def test_true_false_option():
    @dataclass
    class ArgTest:
        true_false: Annotated[bool, cappa.Arg(long="--true/--no-true")] = True

    test = parse(ArgTest)
    assert test.true_false is True

    test = parse(ArgTest, "--true")
    assert test.true_false is True

    test = parse(ArgTest, "--no-true")
    assert test.true_false is False

    with pytest.raises(ValueError, match="unrecognized arguments: --garbage"):
        parse(ArgTest, "--garbage")
