# State

A [cappa.State](cappa.State) is ultimately a thin wrapper around a simple dictionary, that can
be used to share state among different parts of the overall cappa parsing process.

A `state=` argument can be supplied to [parse](cappa.parse) or [invoke](cappa.invoke), which accepts a
`State` instance. If no upfront `State` instance is supplied, one will be constructed automatically
so it can always be assumed to exist.

```{note}
It is also optionally generic over the dict type. So it can be annotated with `TypedDict` to retain
safety over the dict's fields.
```

```python
import cappa
from typing import Any, Annotated, Any
from dataclasses import dataclass

class CliState:
    config: dict[str, Any]


def get_config(key: str, state: State[CliState]):
    return state.state["config"][key]

@dataclass
class Example:
    token: Annotated[str, cappa.Arg(default=cappa.ValueFrom(get_config, key="token"))]


config = load_config()
state = State({"config": config})
cappa.parse(Example, state=state)
```

The above example shows some pre-cappa data/state being loaded and provided to cappa through `state`.
Then some field accesses the shared `state` by getting it dependency injected into the `ValueFrom`
callable.

```{note}
`Arg.parse` and `invoke` functions can **also** accept `State` annotated inputs in order to
be provided with the `State` instance.
```
