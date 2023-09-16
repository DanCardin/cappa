from dataclasses import dataclass
from typing import Annotated

import cappa
import pytest

from tests.utils import parse


@dataclass
class Command:
    a: Annotated[str, cappa.Arg(short=True)]
    b: Annotated[str, cappa.Arg(short=True, required=True)] = "asdf"


def test_required_implicit():
    with pytest.raises(ValueError, match=r"are required: -a"):
        parse(Command, "-b", "b")

    result = parse(Command, "-a", "a", "-b", "b")
    assert result == Command(a="a", b="b")


def test_required_explicit():
    with pytest.raises(ValueError, match=r"are required: -b"):
        parse(Command, "-a", "a")

    result = parse(Command, "-a", "a", "-b", "b")
    assert result == Command(a="a", b="b")
