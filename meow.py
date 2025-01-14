from dataclasses import dataclass
from typing import Annotated

from typing_extensions import Doc

import cappa


@dataclass()
class Foo:
    bar: Annotated[int, Doc("this is helpful")] = 4


help_formatter = cappa.HelpFormatter(
    default_format="Default: {default}."
)

cappa.parse(Foo, help_formatter=help_formatter)

