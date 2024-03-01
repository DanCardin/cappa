from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from typing_extensions import Annotated

import cappa
from cappa.ui import web, run


@dataclass
class Example:
    """I Am a Title.

    Longer Description.
    """

    positional_arg: str = "optional"
    boolean_flag: bool = False
    single_option: Annotated[int | None, cappa.Arg(short=True, help="A number")] = None
    multiple_option: Annotated[
        Literal["one", "two", "three"],
        cappa.Arg(long=True, help="Pick one!"),
    ] = "one"


if __name__ == "__main__":
    run(Example)
    # web(Example, host='0.0.0.0')
