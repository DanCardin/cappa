from __future__ import annotations

from dataclasses import dataclass

import cappa
import pytest
from typing_extensions import Annotated

from tests.utils import backends, parse


@backends
def test_manually_specified_choices(backend):
    @dataclass
    class ArgTest:
        choice: Annotated[str, cappa.Arg(choices=["a", "1"])]

    result = parse(ArgTest, "a")
    assert result.choice == "a"

    result = parse(ArgTest, "1")
    assert result.choice == "1"

    with pytest.raises(cappa.Exit) as e:
        parse(ArgTest, "two", backend=backend)

    message = str(e.value.message).lower()
    assert "invalid choice: 'two' (choose from 'a', '1')" in message
