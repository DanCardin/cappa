from __future__ import annotations

from dataclasses import dataclass

import pytest

import cappa
from cappa import argparse
from tests.utils import Backend, backends, parse


@backends
def test_unbounded_empty_positional_uses_singular_value(backend: Backend):
    """An empty unbounded positional requires 'at least one value' (singular)."""

    @dataclass
    class Args:
        a: list[str]

    with pytest.raises(cappa.Exit) as e:
        parse(Args, backend=backend)
    assert e.value.code == 2

    message = str(e.value.message)
    if backend is argparse.backend:  # pyright: ignore
        assert message == "The following arguments are required: a"
    else:
        assert message == "Argument 'a' requires at least one value, found 0"
