# Commands

A command can be as simple as a dataclass-like object, with no additional
annotations. Supported object-types include:

- dataclasses
- pydantic models
- pydantic dataclasses
- attrs classes

```python
from dataclasses import dataclass

@dataclass
class Dataclass:
    name: str

# or
from pydantic import BaseModel

class PydanticModel(BaseModel):
    name: str

# or

from pydantic.dataclasses import dataclass as pydantic_dataclass

@pydantic_dataclass
class PydanticDataclass:
    name: str

# or
from attr import define

@define
class AttrsClass:
    name: str


from cappa import parse

p1 = parse(Dataclass)
assert isinstance(p1, Dataclass)

p2 = parse(PydanticModel)
assert isinstance(p2, PydanticModel)

p3 = parse(PydanticDataclass)
assert isinstance(p3, PydanticDataclass)

p4 = parse(AttrsClass)
assert isinstance(p4, PAttrsClass)
```

However, you can additionally wrap the class in the `cappa.command` decorator to
gain access to (described below) more customizability and behavior.

```{note}
The wrapped class is directly returned from the decorator. So unlike `click`,
the resultant object can be directly used in the same way that you'd have been
able to do sans decorator.
```

```{eval-rst}
.. autoapimodule:: cappa
   :members: Command
   :noindex:
```

## Command/Subcommand Name

By default, the name of the command is inferred from the name of the containing
class, and converted to dash-case. For example `Example` would become `example`,
and `SomeLongName` would become `some-long-name`.

The `name` field can be used to override this behavior.

## Help/Description Text

```{note}
All of `Command`, `Subcommand`, and `Arg` accept `help` arguments which can
be used to override the default behavior for that item.

Command also accepts a "description", which constitutes the extended text section
below.
```

By default, the help text for commands/subcommands/options will be inferred from
the docstrings of the referenced classes. For example,

```python
class Example:
    """Example CLI.

    With some long description.

    Arguments:
        foo: The number of foos
    """
    foo: int
```

would produce the following help text:

```
Usage: example.py [-h]

Example CLI. With some long description.

Positional Arguments:
  foo                  The number of foos
```

## Invoke

See [Invoke](./invoke.md) documentation for more details. Essentially this
invokes a function upon a command/subcommand being selected during parsing, when
using `cappa.invoke` instead of `cappa.parse`.
