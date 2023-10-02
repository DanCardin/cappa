from __future__ import annotations

from dataclasses import dataclass

import cappa
import pytest

from tests.utils import backends, parse


@backends
def test_default(backend):
    @dataclass
    class ArgTest:
        default: int

    with pytest.raises(cappa.Exit) as e:
        parse(ArgTest, "foo", backend=backend)

    assert e.value.code == 2
    assert (
        e.value.message
        == "Invalid value for 'default' with value 'foo': invalid literal for int() with base 10: 'foo'"
    )
