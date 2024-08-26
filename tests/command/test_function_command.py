from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from typing_extensions import Annotated

import cappa
from tests.utils import backends, invoke, parse


@backends
def test_no_op(backend):
    """Base case, this doesnt really serve any purpose."""

    def function():
        return 4

    parse(function, backend=backend)


@backends
def test_parse_one_arg(backend):
    """Parse with arguments.

    Again, not really a logical usecase for `parse`, but technically it ought to work.
    """

    def function(foo: str):
        return foo

    result = parse(function, "meow", backend=backend)
    assert result.foo == "meow"


@backends
def test_invoke_base_case(backend):
    def function(foo: str):
        return foo

    result = invoke(function, "meow", backend=backend)
    assert result == "meow"


@backends
def test_invoke_optional_args(backend):
    def function(foo: Annotated[int, cappa.Arg(long=True)] = 15):
        return foo

    result = invoke(function, backend=backend)
    assert result == 15

    result = invoke(function, "--foo", "53", backend=backend)
    assert result == 53


@dataclass
class Sub:
    bar: Annotated[int, cappa.Arg(long=True)]

    def __call__(self):
        return self.bar + 1


@backends
def test_subcommand(backend):
    def function(sub: cappa.Subcommands[Union[Sub, None]] = None):
        assert sub is None
        return 6

    result = invoke(function, backend=backend)
    assert result == 6

    result = invoke(function, "sub", "--bar", "34", backend=backend)
    assert result == 35


def foo():
    return 5


@backends
def test_invoke_partial_arg_partial_dep(backend):
    def function(
        dep: Annotated[int, cappa.Dep(foo)],
        foo: Annotated[int, cappa.Arg(long=True)] = 15,
    ):
        return dep + foo

    result = invoke(function, backend=backend)
    assert result == 20

    result = invoke(function, "--foo", "53", backend=backend)
    assert result == 58
