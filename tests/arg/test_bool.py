from __future__ import annotations

from dataclasses import dataclass

import cappa
from typing_extensions import Annotated

from tests.utils import parse


@dataclass
class ArgTest:
    default: bool = False
    explicit_short: Annotated[bool, cappa.Arg(short="-es")] = False
    explicit_long: Annotated[bool, cappa.Arg(long="--meow")] = False
    default_true: Annotated[bool, cappa.Arg(long="--false")] = True


def test_default():
    test = parse(ArgTest)
    assert test.default is False

    test = parse(ArgTest, "--default")
    assert test.default is True


def test_explicit_short():
    test = parse(ArgTest)
    assert test.explicit_short is False

    test = parse(ArgTest, "-es")
    assert test.explicit_short is True


def test_explicit_long():
    test = parse(ArgTest)
    assert test.explicit_long is False

    test = parse(ArgTest, "--meow")
    assert test.explicit_long is True


def test_store_false():
    test = parse(ArgTest)
    assert test.default_true is True

    test = parse(ArgTest, "--false")
    assert test.default_true is False
