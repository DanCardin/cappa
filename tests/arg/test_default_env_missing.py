from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@dataclass
class Command:
    opt: Annotated[str | None, cappa.Arg(default=cappa.Env("DOESNT_EXIST"))]
    opt2: Annotated[
        str | None, cappa.Arg(default=cappa.Env("DOESNT_EXIST", default=None))
    ]
    opt3: Annotated[
        str | None, cappa.Arg(default=cappa.Env("DOESNT_EXIST", default=None))
    ] = None


@backends
def test_env_missing(backend):
    test = parse(Command, backend=backend)
    assert test == Command(None, None, None)


@backends
def test_default_is_not_mapped(backend):
    with patch("os.environ", new={"DOESNT_EXIST": "asdf"}):
        test = parse(Command, backend=backend)

    assert test == Command("asdf", "asdf", "asdf")
