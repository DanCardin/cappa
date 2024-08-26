from __future__ import annotations

from dataclasses import dataclass
from typing import Union

import pytest

import cappa
from tests.utils import backends, parse


@backends
def test_unrecognized_post_dash_arg(backend):
    @dataclass
    class Args:
        foo: str
        raw: Union[str, None] = None

    with pytest.raises(cappa.Exit) as e:
        parse(Args, "foovalue", "raw", "raw2", backend=backend)

    assert e.value.code == 2
    assert "unrecognized arguments: raw2" in str(e.value.message).lower()
