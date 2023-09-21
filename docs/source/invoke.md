# Invoke

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

```{eval-rst}
.. autoapimodule:: cappa
   :members: invoke
   :noindex:
```

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

## Invoke Dependencies

`cappa.invoke` wouldn't be of much value if all it did was call argument-less
functions without any context. Thus, there is a system of "dependencies" that
cause arguments to your invoke functions to be supplied on demand, assuming the
CLI invocation is capable of fullfilling the dependencies.

There are two kinds of invoke dependencies, implicit and explicit.

### Implicit Dependencies

These are objects of the types described in your CLI object heirarchy. That is,

```python
@dataclass
class Subcommand:
    ...

@dataclass
class Command:
    subcommand: Annotated[Subcommand, cappa.Subcommand]
```

`Command` and `Subcommand` are the implicit dependencies available to you in
your invoke functions.

```{note}
If there were another subcommand option, and the CLI invocation selected one or
the other of the two subcommand options, only the selected subcommand would have
been fullfilled.

It's therefore programmer error to describe an `invoke` function heirarchy which
depends on command options that would not have been constructed during parsing.
```

Given the implicit dependencies available to you, your `invoke` functions can
accept an argument of that type, and it will be automatically provided to the
function when invoked.

```python
def foo(command: Command, subcmd: Subcommand):
    ...

@cappa.command(invoke=foo)
...
```

### Explicit Dependencies

```{note}
If you're familiar with FastAPI's `Depends`, this will feel very similar.
```

Custom "explicit dependencies" can be built up, in order to have arbitrary
context injected into your invoked functions. Explicit dependencies must be
annotated with a `Dep` in order to be recognized as such.

```{note}
A function describing an explicit dependency can, itself, depend on other
explicit or implicit dependencies. This allows recursively building up a dependency
heirarchy.
```

```python
from typing_extensions import Annotated
from cappa import Dep

# No more dependencies, ends the dependency chain.
def config():
    return {
        'password': os.getenv('DB_PASS'),
    }


# Explicit dependency
def database(config: Annotated[Engine, Dep(config)]):
    return sqlalchemy.create_engine(...)


# Implicit dependency
def logger(example: Example):
    ...


# The actual invoke function, which can depend upon any/all of the above
def invoke(
    example: Example,
    logger: Annotated[Logger, Dep(logger)],
    database: Annotated[Engine, Dep(database)]
):
    ...
```

- Any dependency can be referenced by any other dependency, or invoked function.
- Dependencies are evaluated only once per `cappa.invoke` call, regardless of
  how many dependencies transitively depend on it.
- Dependencies are evaluated on demand, in the order they're found, meaning they
  will not be evaluated if the specifically invoked function doesn't reference
  it.

### Unfulfilled Dependencies

Should an argument be neither an explicitly annotated `Dep`, nor typed as one of
the available implicit dependencies in the heirarchy, then it's considered
unfulfilled.

If the argument to the callable has a default value, then the argument will
simply be omitted, and the function called anyway.

In the event the argument is required, a `RuntimeError` will be raised and CLI
processing will stop.
