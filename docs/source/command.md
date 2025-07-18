# Commands

A command can be as simple as a dataclass-like object, with no additional
annotations. Supported object-types include:

````{collapse} dataclasses
:open: 

```python
from cappa import parse

from dataclasses import dataclass

@dataclass
class Dataclass:
    name: str

value = parse(Dataclass)
assert isinstance(value, Dataclass)
```
````

````{collapse} Pydantic models
```python
from cappa import parse
from pydantic import BaseModel

class PydanticModel(BaseModel):
    name: str

value = parse(PydanticModel)
assert isinstance(value, PydanticModel)
```
````

````{collapse} Pydantic dataclasses
```python
from cappa import parse
from pydantic.dataclasses import dataclass as pydantic_dataclass

@pydantic_dataclass
class PydanticDataclass:
    name: str

value = parse(PydanticDataclass)
assert isinstance(value, PydanticDataclass)
```
````

````{collapse} Attrs classes
```python
from cappa import parse
from attr import define

@define
class AttrsClass:
    name: str

value = parse(AttrsClass)
assert isinstance(value, AttrsClass)
```
````

````{collapse} cattrs classes
```python
from cappa import parse
from attr import define

@define
class CAttrsClass:
    name: str

value = parse(CAttrsClass)
assert isinstance(value, CAttrsClass)
```
````

An undecorated dataclass-class will receive all the default [cappa.command](cappa.command)
behavior. In order to customize or change the default behavior, you would
begin by wrapping the class in the `@cappa.command` decorator like so:

```python
@cappa.command()
@dataclass
class Dataclass:
    name: str
```

```{note}
The wrapped class is directly returned from the decorator. So unlike `click`,
the resultant object can be directly used in the same way that you'd have been
able to do sans decorator.
```

```{note}
All arguments to [cappa.command](cappa.command) directly translate to [cappa.Command](cappa.Command)
attributes. When annotating an object with `@command()`, you are essentially pre-configuring
the generated [cappa.Command](cappa.Command) for that particular command.
```

## Subcommands

See [Subcommands](./subcommand.md) for details.

In short, any supported dataclass-like class that can be a top-level command is also
compatible with being a subcommand. The only difference is that subcommands
are attached to parent commands in a tree by way of having the parent define which
subcommands are available options.

```python
from cappa import Subcommands

@dataclass
class Command:
    subcommand: Subcommands[SubcmdOne | SubcmdTwo]
```

## `@command(name=...)` / `Command.name`

By default, the name of the command is inferred from the name of the containing
class, and converted to dash-case. For example `Example` would become `example`,
and `SomeLongName` would become `some-long-name`.

The `name` field can be used to override this behavior.

## `@command(help=...)` / `Command.help`

See [Help Text Inference](./help.md) for details.

Essentially this replaces any inferred (from docstring) **short** help text for the command.

## `@command(description=...)` / `Command.description`

See [Help Text Inference](./help.md) for details.

Essentially this replaces any inferred (from docstring) **extended** help text for the command.

## `@command(invoke=...)` / `Command.invoke`

See [Invoke](./invoke.md) documentation for more details.

Essentially this invokes a function upon a command/subcommand being selected during parsing,
corresponds to use of the `cappa.invoke` API rather than `cappa.parse`.

This API is roughly comparable to how `click` maps subcommands to functions.

## `@command(hidden=...)` / `Command.hidden`

Excludes the command in question from parent helptext generation. As such this
option is only relevant to subcommands.

## `@command(default_short=...)` / `Command.default_short`

By default unannotated arguments are considered to be ordered positional aruguments.

This option controls whether un-annotated arguments default to implying [Arg(short=True)](arg-short).

For example:

```python
@command(default_short=True)
@dataclass
class Foo:
    bar: int

# which is then called like:
# `foo -b 4`
```

## `@command(default_long=...)` / `Command.default_long`

By default unannotated arguments are considered to be ordered positional aruguments.

This option controls whether un-annotated arguments default to implying [Arg(long=True)](arg-long).

For example:

```python
@command(default_long=True)
@dataclass
class Foo:
    bar: int

# which is then called like:
# `foo --bar 4`
```

## `@command(deprecated=...)` / `Command.deprecated`

This generates a warning if the command in question is used at runtime.

If `True` is supplied, a default deprecation message is generated. Alternatively
it accepts the string message that should be emitted.

## API

```{eval-rst}
.. autoapiclass:: cappa.Command
   :noindex:
```
