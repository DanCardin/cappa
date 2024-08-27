from __future__ import annotations

from dataclasses import dataclass
from typing import Union

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@backends
def test_(backend):
    @dataclass
    class Args:
        foo: Annotated[str, cappa.Arg(long=True)]
        raw: Annotated[Union[list[str], None], cappa.Arg(num_args=-1)] = None

    with pytest.raises(cappa.Exit) as e:
        parse(Args, "--foo", "--", "value", backend=backend)

    message = str(e.value.message)
    if backend:
        assert "--foo: expected one argument" in message
    else:
        assert "Option 'foo' requires an argument" in message
