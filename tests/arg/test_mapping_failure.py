from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union

import pytest
from typing_extensions import Annotated

import cappa
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
        == "Invalid value for 'default': invalid literal for int() with base 10: 'foo'"
    )


@backends
def test_other_exception_types(backend):
    @dataclass
    class ArgTest:
        path: Annotated[Union[Path, None], cappa.Arg(long=True)] = None

    result = parse(ArgTest, backend=backend)
    assert result.path is None

    result = parse(ArgTest, "--path", "asdf", backend=backend)
    assert result.path == Path("asdf")
