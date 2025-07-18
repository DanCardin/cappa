# Argument Validation

The type system is not always descriptive enough to fully validate all user inputs,
there is sometimes a desire to manually validate input values **before** completing
parsing, or returning control back to the actual program's command implementations.

There are a few options that may be more or less applicable depending on the situation.

1. Take control of [Arg.parse](arg-parse)

This option is very simple, in that it forgos all cappa type inference in favor of the
user provided function. In exchange, you give up the default inference and thus have to
parse the raw input string yourself.

```python
import cappa
from typing import Annotated
from dataclasses import dataclass

def gt_zero(raw_value: str) -> int:
    value = int(raw_value)
    if value <= 0:
        raise ValueError("Value must be greater than zero")
    return value

@cappa.command
@dataclass
class Foo:
    bar: Annotated[int, cappa.Arg(parse=gt_zero)]

print(cappa.parse(Foo))
```

1. Compose your validation with the default [Arg.parse](arg-parse)

You can provide a sequence of `parse` functions, to be called in order, using the
default implementation as the first one. While in this particular example, it might
not be hugely beneficial, for more complex or nested types, the inference may be doing
enough work that it'd be preferable to only layer in your validation on top of the default.

```python
import cappa
from typing import Annotated
from dataclasses import dataclass

def gt_zero(value: int) -> int:
    if value <= 0:
        raise ValueError("Value must be greater than zero")
    return value

@cappa.command
@dataclass
class Foo:
    bar: Annotated[int, cappa.Arg(parse=[cappa.default_parse, gt_zero])]

print(cappa.parse(Foo))
```

1. Utilize class-level construction validation.

Cappa will capture and `ValueError` or `Exit` exceptions raised during the construction
of the underlying dataclasses that comprise your CLI. As such, you can instrument
those classes to perform class-level validation on construction.

```python
import cappa
from dataclasses import dataclass

@cappa.command
@dataclass
class Foo:
    bar: int

    def __post_init__(self):
        if self.bar <= 0:
            raise ValueError("Bar must be greater than zero")

print(cappa.parse(Foo))
```


````{note} Other base classes (e.g. Pydantic, attrs, msgspec)

All of pydantic, attrs, and msgspec either have a similar facility to `__post_init__`
and/or specifically have constraint/validation logic built into their APIs. This
may or may not serve you, as you will not necessarily be able to control the error
messages.

For example, (at least by default) pydantic's error messages include a lot of
code-specific information that might not be appropriate for a CLI user.

However, as you can see, it does produce a very compact class definition
and validation pair.

```python
import cappa
from pydantic import BaseModel, Field

@cappa.command
class Foo(BaseModel):
    bar: int = Field(gt=0)

print(cappa.parse(Foo))
```

With that said, all 3 options produce `ValueError`-based exceptions on validation
errors, and will do the correct thing with regards to cappa.
````

1. Custom [Arg.action](arg-action)

As usual, custom actions should probably only be considered as a last resort,
because you're giving up most of the argument parsing infrastructure in exchange
for control over how the data is written.

With that said, anything you can do with a `Arg.parse` function, you can do with
and `Arg.action`, and then some.
