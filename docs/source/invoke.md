# Invoke Dependencies

`cappa.invoke` wouldn't be of much value if all it did was call argument-less
functions without any context. Thus, there is a system of "dependencies" that
cause arguments to your invoke functions to be supplied on demand, assuming the
CLI invocation is capable of fullfilling the dependencies.

There are two kinds of invoke dependencies, implicit and explicit.

## Implicit Dependencies

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

## Explicit Dependencies

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

## Unfulfilled Dependencies

Should an argument be neither an explicitly annotated `Dep`, nor typed as one of
the available implicit dependencies in the heirarchy, then it's considered
unfulfilled.

If the argument to the callable has a default value, then the argument will
simply be omitted, and the function called anyway.

In the event the argument is required, a `RuntimeError` will be raised and CLI
processing will stop.
