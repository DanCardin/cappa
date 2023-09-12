# Cappa

Cappa is a more declarative take on command line parsing library, which takes
much of its inspiration from Rust's
[Clap](https://docs.rs/clap/latest/clap/_derive/index.html) library('s derive
API).

```python
from __future__ import annotations

import cappa
from typing import Annotated
from dataclasses import dataclass


@dataclass
class Example:
    """Example program

    Args:
       name: Required name argument
       flag: optional flag to enable
    """

    name: str  # positional arg
    flag: bool  # --flag
    flags: Annotated[list[str], cappa.Arg(short=True, long=True)]
    value: Annotated[int, cappa.Arg(short="-v", long="--val")]

    subcommand: Annotated[MeowCommand | BarkCommand, cappa.Subcommand]


@dataclass
class MeowCommand:
    ...


def bark(bark: BarkCommand):
    print(bark)


@cappa.command(name="bark", invoke=bark)
@dataclass
class BarkCommand:
    ...


# invoke cli parsing
def main():
    args: Example = cappa.parse(Example)
    print(args)
    ...


    # Or click-like automatic invocation of the command, where `example bark` would call `bark`.
    cappa.exec(Example)
```

Generates CLI help text like:

```
[-h] --flag -f FLAGS -v VALUE name {meow-command,bark} ...

Example program

positional arguments:
  name                  Required name argument

options:
  -h, --help            show this help message and exit
  --flag                optional flag to enable
  -f FLAGS, --flags FLAGS
  -v VALUE, --val VALUE

subcommand:

  {meow-command,bark}
    meow-command        MeowCommand()
    bark                BarkCommand()
```

## Invoke

Accepts either of:

- `@cappa.command(invoke=function)`
- `@cappa.command(invoke='module.submodule.function')` (which imports the given
  module/function given as a string)

Use of the `invoke` kwarg on a command allows you to get click-like invocation
based on the command/subcommand given by argv.

For example, `cli foo bar baz --flag`, might have a corresponding
`@cappa.command(name='baz', invoke=baz)` command defined, which will cause `baz`
to be called.

You would opt into this behavior by calling `cappa.exec(Cli)`.

### Invoke Dependencies

In the above example, the injected `bark` argument is an example of an "implicit
dependency", which is fullfilled automatically by the parsing of the cli input
structures themselves.

Custom "explicit dependencies" can be referenced in order to have arbitrary
context injected into your invoked functions.

```python
import os
from cappa import Arg, command, Dep, invoke, unpack
from dataclasses import dataclass
from typing import Annotated

def foo(
    foo: Foo,  # An "implicit dependency"
    verbose: Annotated[Foo, unpack(Foo, 'verbose')],  # An "explicit dependency". In this case,
                                                      # using a built-in function for extracting
                                                      # fields from an "implicit" dependency.

    session: Annotated[str, Dep(db_session)]  # An "explicit dependency" with an arbitrary function
                                              # that provides the required value.
):
    ...


def db_session(config: Annotated[dict, Dep(load_config)]):  # Note, dependencies can be recursively loaded.
    return ...


def load_config():  # And dependencies are terminated once one is reached that has no other dependencies.
    return {
        "username": os.getenv("DB_USER"),
    }


@cappa.command(invoke=foo)
@dataclass()
class Foo:
    verbose: Annotated[int, Arg(count=True)]
```

- Any dependency can be referenced by any other dependency, or invoked function.
- Dependencies are evaluated in the order they are reached, and only evaluated
  once.
- Dependencies are evaluated on demand, and will not be evaluated if the
  specifically invoked function doesn't in some transitive way reference it.

## Internals

Internally, cappa is (currently) implemented on top of the built-in `argparse`
library. However, all of the commandline parsing logic is centrally factored,
and the **actual** library/code underlying the parsing should be considered an
implementation detail.

## Todo

- Enum should coerce to choices
- unions are choices, so literal union of strings should be click-like string
  choices
- ```python
  cappa.parse(Example, commands=[
    # i.e. is a function
    (BarkCommand, cappa.command(name='bark')),
    # i.e. is a dict
    (BarkCommand, dict(name='bark')),
  ])
  ```

- Wrap argparse's FileType thingy to produce an already opened file buffer with
  the indicated options
- abstract references to dataclasses in parsing to a `class_inspect.py`, to
  support dataclasses, pydantic, attrs. basically just to iterate the fields and
  access the annotations
