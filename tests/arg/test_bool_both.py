from __future__ import annotations

from dataclasses import dataclass

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import Backend, backends, parse


@backends
def test_missing_default(backend: Backend):
    @dataclass
    class Args:
        foo: Annotated[bool, cappa.Arg(long="--foo/--no-foo")] = False

    test = parse(Args, backend=backend)
    assert test.foo is False

    test = parse(Args, "--foo", backend=backend)
    assert test.foo is True

    with pytest.raises(cappa.Exit) as e:
        parse(Args, "--foo", "--no-foo", backend=backend)

    message = str(e.value.message)
    assert "--no-foo" in message
    assert "--foo" in message
    assert "not allowed with argument" in message
