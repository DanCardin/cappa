from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@cappa.command(name="insiders")
@dataclass
class Args:
    arg: Annotated[int, cappa.Arg(short="-ab")]
    foo: Annotated[bool, cappa.Arg(short="-bc")] = False


@backends
def test_single_opt(backend):
    args = parse(Args, "-ab", "1", backend=backend)
    assert args == Args(arg=1, foo=False)
