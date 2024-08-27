from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@backends
def test_num_args_unbounded_length_num_args(backend):
    @dataclass
    class Args:
        a: Annotated[list[str], cappa.Arg(short=True, num_args=-1)] = field(
            default_factory=list
        )
        b: Annotated[str, cappa.Arg(short=True)] = field(default="")
        foo: Optional[str] = None

    # Unbounded length by itself
    t1 = parse(Args, backend=backend)
    assert t1 == Args(a=[], foo=None)

    # Unbounded length by itself
    t1 = parse(Args, "-a", "1", "2", "3", backend=backend)
    assert t1 == Args(a=["1", "2", "3"], foo=None)

    # An option can follow to terminate the option
    t1 = parse(Args, "-a", "1", "2", "3", "-b", "b", "foo", backend=backend)
    assert t1 == Args(a=["1", "2", "3"], b="b", foo="foo")

    # Or the -- separator can be used to terminate it
    t1 = parse(Args, "-a", "1", "2", "3", "--", "foo", backend=backend)
    assert t1 == Args(a=["1", "2", "3"], foo="foo")
