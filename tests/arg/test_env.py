from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import cappa
from typing_extensions import Annotated

from tests.utils import parse


def test_missing_fallback():
    @dataclass
    class ArgTest:
        default: Annotated[str, cappa.Arg(default=cappa.Env("ASDF", default="wat"))]

    test = parse(ArgTest)
    assert test.default == "wat"


def test_has_env_var():
    @dataclass
    class ArgTest:
        default: Annotated[str, cappa.Arg(default=cappa.Env("ASDF", default="wat"))]

    with patch("os.environ", new={"ASDF": "asdf!"}):
        test = parse(ArgTest)
    assert test.default == "asdf!"


def test_env_defers_to_real_value():
    @dataclass
    class ArgTest:
        default: Annotated[str, cappa.Arg(default=cappa.Env("ASDF", default="wat"))]

    test = parse(ArgTest, "test")
    assert test.default == "test"


def test_mapping_is_applied():
    @dataclass
    class ArgTest:
        default: Annotated[bool, cappa.Arg(default=cappa.Env("ASDF", default="wat"))]

    test = parse(ArgTest)
    assert test.default is True
