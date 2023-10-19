from dataclasses import dataclass

import cappa
from typing_extensions import Annotated

from tests.utils import backends, parse


@cappa.command(name="insiders")
@dataclass
class Args:
    arg: Annotated[int, cappa.Arg(short="-a", long=True)]
    foo: Annotated[bool, cappa.Arg(short="-f", long=True)] = False
    bar: Annotated[bool, cappa.Arg(short="-b", long=True)] = False


@backends
def test_single_option_value_no_space(backend):
    args = parse(Args, "-a0", backend=backend)
    assert args == Args(arg=0, foo=False, bar=False)


@backends
def test_single_option_value_equals(backend):
    args = parse(Args, "-a=0", backend=backend)
    assert args == Args(arg=0, foo=False, bar=False)


@backends
def test_mulitple_option_no_space(backend):
    args = parse(Args, "-fba0", backend=backend)
    assert args == Args(arg=0, foo=True, bar=True)
