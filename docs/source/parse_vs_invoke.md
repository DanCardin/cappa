# Parse Vs Invoke

The choice to use [cappa.parse](cappa.parse) or [cappa.invoke](cappa.invoke)
boils down to whether you prefer an `argparse`-style CLI or a `click`-style CLI.

Given some basic CLI:

```python
from dataclasses import dataclass
from typing import Annotated

import cappa

@dataclass
class Example:
    flag: bool
    name: Annotated[str, cappa.Arg(long=True)]
```

For an `argparse`-style experience, you would opt for
[cappa.parse](cappa.parse), preferring to let the library **just** parse the
commandline arguments and hand you an `Example` instance like so:

```python
def main():
    result: Example = cappa.parse(Example)
    # Do things with your Example instance...
    if example.flag:
        print(example.name)
```

Alternatively, if you prefer a `click`-style experience, you're used to
decorating a function with a few command/option decorators and letting click
take care of calling your function with the appropriate arguments.

You would instead use [cappa.invoke](cappa.invoke), like so:

```python
def example(ex: Example):
    if example.flag:
        print(example.name)


@cappa.command(invoke=example)
class Example
    ... # your original example body


cappa.invoke(Example)
```

Note, in a basic example like this, `invoke` has essentially no advantage at
all. When used in a command with subcommands (with their own `invoke` options)
it becomes more useful! When used with [Deps](./invoke.md#invoke-dependencies),
it becomes more useful still.
