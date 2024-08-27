from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@backends
def test_missing_fallback(backend):
    @dataclass
    class ArgTest:
        default: Annotated[str, cappa.Arg(default=cappa.Env("ASDF", default="wat"))]

    test = parse(ArgTest, backend=backend)
    assert test.default == "wat"


@backends
def test_has_env_var(backend):
    @dataclass
    class ArgTest:
        default: Annotated[str, cappa.Arg(default=cappa.Env("ASDF", default="wat"))]

    with patch("os.environ", new={"ASDF": "asdf!"}):
        test = parse(ArgTest, backend=backend)
    assert test.default == "asdf!"


@backends
def test_env_defers_to_real_value(backend):
    @dataclass
    class ArgTest:
        default: Annotated[str, cappa.Arg(default=cappa.Env("ASDF", default="wat"))]

    test = parse(ArgTest, "test", backend=backend)
    assert test.default == "test"


@backends
def test_mapping_is_applied(backend):
    @dataclass
    class ArgTest:
        default: Annotated[bool, cappa.Arg(default=cappa.Env("ASDF", default="wat"))]

    test = parse(ArgTest, backend=backend)
    assert test.default is True


@backends
def test_class_default_gets_applied_to_env_default(backend):
    @dataclass
    class ArgTest:
        default: Annotated[str, cappa.Arg(default=cappa.Env("ASDF"))] = "wat"

    test = parse(ArgTest, backend=backend)
    assert test.default == "wat"


@backends
def test_class_default_still_abides_env_var(backend):
    @dataclass
    class ArgTest:
        default: Annotated[str, cappa.Arg(default=cappa.Env("ASDF"))] = "wat"

    with patch("os.environ", new={"ASDF": "foo"}):
        test = parse(ArgTest, backend=backend)
    assert test.default == "foo"
