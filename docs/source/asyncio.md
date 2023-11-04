# Asyncio

```{note}
Asyncio support was added in v0.12.0.
```

Cappa supports asyncio through the [cappa.invoke_async](cappa.invoke_async)
function, which has an identical interface to [cappa.invoke](cappa.invoke),
**except** in that it is an async function.

Given that it is an async function, it must either be called from an async
function itself, or be invoked through `asyncio.run` or equivalent functions.

By using `invoke_async`, you gain the ability to reference async functions as
invoke targets and as explicit dependencies.

```python
import asyncio
from dataclasses import dataclass

import cappa

def config() -> dict:
    return {'db_password': 'password'}


async def engine(config: Annotated[dict, cappa.Dep(config)]):
    return await create_engine(config)


async def handler(engine: Annotated[int, cappa.Dep(engine)]):
    ...


@cappa.command(invoke=handler)
@dataclass
class Command:
    foo: str
```

```{note}
Since cappa defers the actual async scheduling to the caller, it should
support all asyncio runtimes, including asyncio, trio, curio, etc.
```
