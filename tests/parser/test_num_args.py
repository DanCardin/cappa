from dataclasses import dataclass

import cappa
import pytest
from typing_extensions import Annotated

from tests.utils import backends, parse


def action():
    raise cappa.Exit()


@dataclass
class Args:
    kill_switch: Annotated[bool, cappa.Arg(long="--kill", action=action, num_args=0)]
    required: str


@backends
def test_single_opt(backend):
    with pytest.raises(cappa.Exit) as e:
        parse(Args, "--kill", backend=backend)

    assert e.value.message is None
    assert e.value.code == 0
