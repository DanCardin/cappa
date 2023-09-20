from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import cappa

from tests.utils import parse


@dataclass
class ArgTest:
    default: bool = False
    explicit_short: Annotated[bool, cappa.Arg(short="-es")] = False
    explicit_long: Annotated[bool, cappa.Arg(long="--meow")] = False


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
