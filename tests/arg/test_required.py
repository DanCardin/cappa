from dataclasses import dataclass

import cappa
import pytest
from typing_extensions import Annotated

from tests.utils import backends, parse


@dataclass
class Command:
    a: Annotated[str, cappa.Arg(short=True)]
    b: Annotated[str, cappa.Arg(short=True, required=True)] = "asdf"


@backends
def test_required_implicit(backend):
    with pytest.raises(cappa.Exit) as e:
        parse(Command, "-b", "b", backend=backend)

    assert e.value.code == 2
    assert "are required: -a" in str(e.value.message)

    result = parse(Command, "-a", "a", "-b", "b", backend=backend)
    assert result == Command(a="a", b="b")


@backends
def test_required_explicit(backend):
    with pytest.raises(cappa.Exit) as e:
        parse(Command, "-a", "a", backend=backend)

    assert e.value.code == 2
    assert "are required: -b" in str(e.value.message)

    result = parse(Command, "-a", "a", "-b", "b")
    assert result == Command(a="a", b="b")


@backends
def test_required_lists_all(backend):
    with pytest.raises(cappa.Exit) as e:
        parse(Command, backend=backend)

    assert e.value.code == 2
    assert "are required: -a, -b" in str(e.value.message)
