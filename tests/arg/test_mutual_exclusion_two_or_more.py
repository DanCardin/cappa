from __future__ import annotations

from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from cappa.output import Exit
from tests.utils import Backend, backends, parse


@dataclass
class Args:
    verbose: Annotated[
        int,
        cappa.Arg(short="-v", action=cappa.ArgAction.count),
        cappa.Arg(long="--verbosity"),
    ] = 0
    meow: Annotated[bool, cappa.Arg(long="--meow/--no-meow")] = False
    bar: Annotated[bool, cappa.Arg(long="--bar/--no-bar")] = False


@backends
def test_help(backend: Backend | None):
    result = parse(Args, "-vvv", "--meow", "--no-bar", backend=backend)
    assert result == Args(verbose=3, meow=True, bar=False)

    result = parse(Args, "--verbosity=4", "--no-meow", "--bar", backend=backend)
    assert result == Args(verbose=4, meow=False, bar=True)

    with pytest.raises(Exit) as e:
        parse(Args, "-vvv", "--verbosity=4", backend=backend)

    if backend is None:
        expected = "Argument '--verbosity' is not allowed with argument '-v'"
    else:
        expected = "argument --verbosity: not allowed with argument -v"
    assert expected.lower() in str(e.value.message).lower()

    with pytest.raises(Exit) as e:
        parse(Args, "--meow", "--no-meow", backend=backend)
    if backend is None:
        expected = "Argument '--no-meow' is not allowed with argument '--meow'"
    else:
        expected = "argument --no-meow: not allowed with argument --meow"
    assert expected.lower() in str(e.value.message).lower()

    args = parse(Args, "--no-bar", "--meow", backend=backend)
    assert args == Args(verbose=0, meow=True, bar=False)
