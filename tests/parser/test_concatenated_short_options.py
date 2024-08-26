from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


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


@backends
def test_distinguish_short_args_with_args_from_without(backend):
    # Only short args which consume no additional values (i.e. flags) should
    # be captured as concatenated short args. With arg which consumes a value,
    # subsequent characters should be given as part of the "arg" portion of
    # the value
    @dataclass
    class Args:
        arg: Annotated[str, cappa.Arg(short="-a")]
        foo: Annotated[bool, cappa.Arg(short="-f")] = False

    args = parse(Args, "-fahello world", backend=backend)
    assert args == Args(arg="hello world", foo=True)
