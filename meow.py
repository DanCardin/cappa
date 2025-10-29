import asyncio
from dataclasses import dataclass
from typing import Annotated, TypeVar

from rich.prompt import IntPrompt

import cappa
from cappa import ValueFrom

T = TypeVar("T")


async def test() -> list[int]:
    return [1]


async def gen() -> int:
    ids = await test()
    business = IntPrompt.ask("choices a business", choices=[str(_id) for _id in ids])
    return business


@dataclass
class Test:
    business: Annotated[
        int,
        cappa.Arg(default=ValueFrom(gen), help="Business ID"),
    ]

    async def __call__(self):
        print(self.business)


asyncio.run(cappa.invoke_async(Test))
