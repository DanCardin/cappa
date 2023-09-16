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
    cappa.invoke(Example)
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

## Annotations

Cappa only uses the `command` decorator and `Arg` annotation for controlling
specific input fields' CLI-parsing-specific details (help text, argument/flag
name, etc).

That is, `cappa.parse/invoke`ing a plain class (dataclass/pydantic model/attrs
class) with plain python type annotations is a perfectly valid thing to do.

Without such annotations, there is a default behavior:

- A command name is inferred to be the `ClassName` converted to dash-case
- A command help text is inferred to be its docstring description
- An argument name is inferred to be the class attribute name
- An argument (class attribute) is inferred to be positional, except booleans
  (which are `--flag`s).
- An argument help text is inferred to be the (numpy/google) docstring argument
  description

Wherein the default

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

## Why?

> Why not click?

I've used click for years, it's certainly a good library. There are some aspects
of its design that make it really frustrating to use beyond small projects with
a single entrypoint.

- Many of the issues stem from the fact that click wraps the called function,
  and changes its behavior. Calling the resultant function invokes the CLI.

  You want to call that function in two places? you need to use `click.invoke`.

  You want to do this in tests? You need to deal with its `ClickRunner` that
  accepts args as a list of string, and output in terms of stdout and stderr. In
  terms of tests, this is really large drop in UX relative to a plain function
  (with args) you can call.

  You want to avoid click-isms in either case? You need to (basically) duplicate
  your function. One wrapped in click decorators, which just defers to a similar
  function that just accepts the arguments.

  - `Cappa` inverts the relationship to invoked functions. You do not wrap the
    functions, so they end up just being plain functions you can call in any
    scenario.

    And in the case of the decorated classes, the resultant class is directly
    returned. It should act exactly like the dataclass/pydantic model you
    defined.

    Even parsing or invoking the CLI through `Cappa`'s mechanisms to parse the
    argv, in tests for example, the result is **much** more similar to just
    executing the function in the first place.

- Click imperitively accumulates the CLI's shape based on where/how you combine
  groups and commands. Intuiting what resultant CLI looks like from the series
  of click commands strung together is not obvious.

  - `Cappa` centrally declares the CLI shape based on types. For all of the
    reasons pydantic models can be easily used to describe a potentially deeply
    nested schema, with `Cappa` it's very easy to look at the model and
    determine the total set of arguments and subcommands relative to it.

- Because click tightly couples the called function with click itself, a large
  enough CLI will inevitably slow down starup because you're forced to
  transitively import your whole codebase in order to describe the state of the
  CLI itself.

  - `Cappa` allows you to define the CLI in a way where you **could** define the
    CLI shape/calls in complete isolation with no (lazy) imports to the rest of
    your code.

- The Click "Context" appears to be its only mechanism for providing
  non-argument dependencies to commands/subcommands. And `pass_context` (and the
  mutation of the context) is a very blunt tool, that secretly couples the
  implementations of different commands together.

  - `Cappa` uses the same dependency resolution mechanisms it uses for arguments
    to provide the result of arbitrary functions to your commands (Reminiscent
    of FastAPI's `Depends`).

    For example, some subcommand require loading config, some commands require a
    database connection (or whatever) which itself depends on that config. What
    would be a, relatively, more difficult task using the click context (or
    manually littering the loading of these things inside the bodies of the
    commands) uses the same API as the rest of `Cappa`.

- With `click`, it's impossible(? or at least not clear how) to perform
  `argparse`-like (or Clap) ability to just parse the structure and return the
  parsed output shape.

  - `Cappa` provides a separate `parse` function and `invoke` function. You can
    choose either style, or both.

> Okay, so you like types, why not [Typer](https://typer.tiangolo.com/)

Typer has a lot of good ideas, inspired by Hug before it. While the actual
inspiration for Cappa is
[Clap](https://docs.rs/clap/latest/clap/_derive/index.html), the annotation
results for arguments end up looking a lot like typer's args!

Unfortunately, Typer is **basically** Click (with type-inferred arguments), and
has all of the same drawbacks.

## Internals

Internally, cappa is (currently) implemented on top of the built-in `argparse`
library. However, all of the commandline parsing logic is centrally factored,
and the **actual** library/code underlying the parsing should be considered an
implementation detail.

## Todo

- Enum should coerce to choices
- Wrap argparse's FileType thingy to produce an already opened file buffer with
  the indicated options
