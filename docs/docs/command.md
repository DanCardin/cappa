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
   :members: command
   :noindex:
```

## Subcommands

As you'll have already seen throughout the documentation, before now.
Subcommands are expressed by annotating a union of subcommand options, and
annotating the union with `cappa.Subcommand`. I.e.

```python
@dataclass
class OptionOne:
    ...

@dataclass
class OptionTwo:
    ...

@dataclass
class Command:
    subcommand: Annotated[OptionOne | OptionTwo, cappa.Subcommand]
```

You can annotate with either the `Subcommand` class, or an instance of it
(should you need to supply options)

```{eval-rst}
.. autoapimodule:: cappa
   :members: Subcommand
   :noindex:
```

## Command/Subcommand Name

By default, the name of the command is inferred from the name of the containing
class, and converted to dash-case. For example `Example` would become `example`,
and `SomeLongName` would become `some-long-name`.

The `name` field can be used to override this behavior.

## Help Text

```{note}
All of `Command`, `Subcommand`, and `Arg` accept `help` arguments which can
be used to override the default behavior for that item.
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

If you're coming from `click` or `typer`, then `invoke` may likely be how you'll
want to describe your commands.

```{note}
See [Invoke Dependencies](./invoke.md) for more information about providing
context/dependencies to your invoked functions.
```

The `invoke` argument should be supplied a reference to a function that should
be called in the event that the parsed CLI invocation targeted the given
command/subcommand.

For a vanilla command, that means the function is simply called. For
subcommands, where there may be one `invoke` function per subcommand option
(maybe, plus one for the top-level command), this means that only the selected
subcommand's `invoke` function will be called.

Then, in order to cause the function to be invoked, you would call
`cappa.invoke`, rather than `cappa.parse`.

```python
from dataclasses import dataclass
from typing_extensions import Annotated

import cappa

def option_one():
    print('option-one')

@cappa.command(invoke=option_one)
@dataclass
class OptionOne:
    ...

def option_two():
    print('option-two')

@cappa.command(invoke=option_two)
@dataclass
class OptionTwo:
    ...


def example():
    ...

@cappa.command(invoke=example)
@dataclass
class Example:
    options: Annotated[OptionOne | OptionTwo | None, cappa.Subcommand] = None


cappa.invoke(Example)
```

- `example.py` would call `example`
- `example.py option-one` would call `option_one`
- `example.py option-two` would call `option_two`

## Implicit invoke imports

The `invoke` argument can be a direct reference to a function, as evidenced in
the single-file documentation examples.

However it can also be a string. When given as a string, it implies a fully
qualified module reference to a function. That is,
`src/package/module/submodule.py` with function `foo` in it, would be given be
the string `package.module.submodule.foo`.

```python
@cappa.command(invoke='package.module.submodule.foo')
@dataclass
class Example:
    ...
```

This can help to solve an issue that can be somewhat endemic to `click`
applications. Namely, that the act of describing the CLI shape forces the
programmer to transitively import all of the code that the CLI might ever
reference in any of its subcommands, regardless of whether they're actually
called in the actual command selected.

The usual approach, in click, is to inline imports into the click handler, thus
achieving the same thing. With cappa, it's much the same thing, except for the
inversion of control. The dynamic import is performed inside the `invoke` call,
which is mostly just a net reduction in boilerplate.
