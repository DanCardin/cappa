# Cappa

[![Actions Status](https://github.com/DanCardin/cappa/actions/workflows/test.yml/badge.svg)](https://github.com/dancardin/cappa/actions)
[![Coverage Status](https://coveralls.io/repos/github/DanCardin/cappa/badge.svg?branch=main)](https://coveralls.io/github/DanCardin/cappa?branch=main)
[![Documentation Status](https://readthedocs.org/projects/cappa/badge/?version=latest)](https://cappa.readthedocs.io/en/latest/?badge=latest)

- [Full documentation here](https://cappa.readthedocs.io/en/latest/).
- [Comparison vs existing libraries.](https://cappa.readthedocs.io/en/latest/comparison.html).
- [Annotation inference details](https://cappa.readthedocs.io/en/latest/annotation.html)
- ["invoke" (click-like) details](https://cappa.readthedocs.io/en/latest/invoke.html)

Cappa is a declarative command line parsing library, taking much of its
inspiration from the "Derive" API from the
[Clap](https://docs.rs/clap/latest/clap/_derive/index.html) written in Rust.

```python
from dataclasses import dataclass
import cappa
from typing_extensions import Annotated


@dataclass
class Example:
    positional_arg: str
    boolean_flag: bool
    single_option: Annotated[int | None, cappa.Arg(long=True)]
    multiple_option: Annotated[list[str], cappa.Arg(short=True)]


args: Example = cappa.parse(Example)
```

Produces the following CLI:

```
meow.py --boolean-flag [--single-option single_option] -m
               multiple_option [-h]
               positional_arg

Positional Arguments:
  positional_arg

Options:
  --boolean-flag
  --single-option single_option
  -m multiple_option

Help:
  -h, --help            Show this message and exit
```

In this way, you can turn any dataclass-like object (with some additional
annotations, depending on what you're looking for) into a CLI.

You'll note that `cappa.parse` returns an instance of the class. This API should
feel very familiar to `argparse`, except that you get the fully typed dataclass
instance back instead of a raw `Namespace`.

## Invoke

["invoke" documentation](https://cappa.readthedocs.io/en/latest/invoke.html)

The "invoke" API is meant to feel more like the experience you get when using
`click` or `typer`. You can take the same dataclass, but register a function to
be called on successful parsing of the command.

```python
from dataclasses import dataclass
import cappa
from typing_extensions import Annotated

def function(example: Example):
    print(example)

@cappa.command(invoke=function)
class Example:  # identical to original class
    positional_arg: str
    boolean_flag: bool
    single_option: Annotated[int | None, cappa.Arg(long=True)]
    multiple_option: Annotated[list[str], cappa.Arg(short=True)]


cappa.invoke(Example)
```

(Note the lack of the dataclass decorator. You can optionally omit or include
it, and it will be automatically inferred).

Alternatively you can make your dataclass callable, as a shorthand for an
explcit invoke function:

```python
@dataclass
class Example:
    ...   # identical to original class

    def __call__(self):
       print(self)
```

Note `invoke=function` can either be a reference to some callable, or a string
module-reference to a function (which will get lazily imported and invoked).

With a single top-level command, the click-like API isn't particularly valuable
by comparison. Click's command-centric API is primarily useful when composing a
number of nested subcommands.

## Subcommands

The useful aspect of click's functional composability is that you can define
some number of subcommands functions under a parent command, whichever
subcommand the function targets will be invoked.

```python
import click

@click.group('example')
def example():
    ...

@example.command("print")
@click.option('--loudly', is_flag=True)
def print_cmd(loudly):
    if loudly:
      print("PRINTING!")
    else:
      print("printing!")

@example.command("fail")
@click.option('--code', type: int)
def fail_cmd(code):
    raise click.Exit(code=code)

# Called like:
# /example.py print
# /example.py fail
```

Whereas with argparse, you'd have had to manually match and call the funcitons
yourself. This API does all of the hard parts of deciding which function to
call.

Similarly, you can achieve the same thing with cappa.

```python
from __future__ import annotations
from dataclasses import dataclass
import cappa

@dataclass
class Example:
    cmd: cappa.Subcommands[Print | Fail]


def print_cmd(print: Print):
    if print.loudly:
        print("PRINTING!")
    else:
        print("printing!")

@cappa.invoke(invoke=print_cmd)
class Print:
    loudly: bool

@dataclass
class Exit:
    code: int

    def __call__(self):  # again, __call__ is shorthand for the above explicit `invoke=` form.
        raise cappa.Exit(code=code)

cappa.invoke(Example)
```
