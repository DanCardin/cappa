# Function/Method Based Commands

## Methods

Methods can be used as a shorthand to define (typically terminal) subcommands.
With methods, the enclosing class corresponds to the parent object CLI arguments,
exactly like normal class based definition. Unlike with free functions, (explicitly
annotated) methods are able to act as subcommands, who's arguments (similarly to free functions)
act as the arguments for the subcommand.

While there's nothing **stopping** one from using the `parse` API with a CLI defined
with methods, it's really only obviously useful in the context of the `invoke` API.

```python
from __future__ import annotations
from dataclasses import dataclass
import cappa

@cappa.command
@dataclass
class Example:
    arg: int

    @cappa.command
    def add(self, other: int) -> int:
        """Add two numbers."""
        return self.arg + some_dep

    @cappa.command(help="Subtract two numbers")
    def subtract(self, other: int) -> int:
        return self.arg - other

cappa.invoke(Example)
```

```{note}
At present any enclosing class which defines method subcommands **must** itself
be decorated with `@cappa.command`. This is **not** true for "traditionally" defined
class-based CLIs.

**Currently** with this style, the resultant class is (secretly) a subclass
of the provided one, which adds a hidden `__cappa_subcommand__` attribute used
to store the subcommand's CLI argument data.

This should 100000% not be relied upon to exist, and may break at any time. Ideally
the need for this internal hack will be resolved in the future.
```
