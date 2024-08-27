# Help

## Help Inference

Cappa tries to infer help text from a variety of sources, preferring them in
descending order of priority:

- An explicit `help=` argument
- A PEP-727 `Doc` annotation
- The class "attribute docstring"
- The class docstring argument description

If none of the above sources produce help text, no description will be rendered.

### Explicit `help=`

All of `Command`, `Subcommand`, and `Arg` accept a `help` argument, which will
take priority over any other existent form of help text inference.

```python
from typing import Annotated
import cappa

@cappa.command(help='Command help')
class Command:
    arg: Annotated[str, Arg(help='Arg help')]
    arg: Annotated[Sub, cappa.Subcommand(help='Subcommand help')]
```

### PEP-727 `Doc` annotation

[PEP-727](https://peps.python.org/pep-0727/) proposes adding a `typing.Doc`
object, in an attempt to standardize the location tooling must handle in order
to find documentation. **If** accepted, this is currently targeted to land in
python 3.13.

As of `typing_extensions` version 4.8.0, there exists a `typing_extensions.Doc`
object, which preemptively will fall back to the `typing` definition if defined.

If PEP-727 is ultimately rejected, this variant may or may not be abruptly
removed, it would entirely depend upon `typing_extensions`'s reaction to the
rejection.

When found, a `Doc` annotation will be used to infer help text, unless
explicitly overridden by a `help=` argument.

```python
from typing import Annotated
from typing_extensions import Doc
import cappa

@cappa.command
class Command:
    arg: Annotated[str, Doc('Arg help')]
```

### Class "attribute docstring" Parsing

An "attribute docstring" is a common convention whereby a declarative class attribute
is "annotated" similarly to a class docstring. For example:

```python
from dataclasses import dataclass

@dataclass
class Command:
    arg: int
    """This arg is an int."""
```

```{note}
Attribute docstrings are not a first-class concept in python today, although
there is a [rejected PEP](https://peps.python.org/pep-0224/) associated with
the idea.

As such, `ast` traversal is required to obtain it, which implies a requirement
that `ast.getsource` be able to function on the given source class. For most
typical user-written situations this should not be an issue, but it's worth
noting the relative complexity involved with this option.
```

### Class Docstring Parsing

```{note}
Docstring parsing is provided by the `docstring-parser` dependency. You can
include this dependency through cappa with the `docstring` extra (`cappa[docstring]`).
```

In the event other sources of help text are not found, the command class'
docstring will be parsed, supporting either Google or Numpy styles of docstring
formatting.

- The short and long docstring descriptions are inferred as extended
  command-level help text
- Argument descriptions are inferred from the arguments list within the
  docstring

```python
from typing import Annotated
import cappa

@cappa.command
class Command:
    arg: Annotated[str, Doc('Arg help')]
```

```python
class Example:
    """Example CLI.

    With some long description.

    Arguments:
        foo: The number of foos
    """
    foo: int
```

would produce something like the following help text:

```
Usage: example.py [-h]

Example CLI. With some long description.

Positional Arguments:
  foo                  The number of foos
```

## Argument Help Formatting

By default, help text is composed from a few sources:

- The actual help text (as described above)
- The default argument value (if exists)
- The set of available "choices" (if exists) (for `Enum`, `Literal`, and `choices=[...]`)

This can be controlled through the use of the `help_formatter` argument to the root
`cappa.parse`, `cappa.invoke`, etc functions. Additionally it can be set on a
per-command/subcommand level by making use of the `@cappa.command(help_formatter=...)`
kwarg.

```{eval-rst}
.. autoapiclass:: cappa.HelpFormatter
```

### Customize "default" help representation

By default, the default value will be rendered into the help text as `(Default: {default})`.

You can customize this, by altering the default `help_formatter`:

```python
from cappa import parse, HelpFormatter

class Command:
    ...

parse(Command, help_formatter=HelpFormatter(default_format="(Default `{default}`)"))
```

### Customizing help formatter "sources"

The default `arg_format` is `("{help}", "{choices}", "{default}")`. That means, given
some argument: `foo: Annotated[Literal["one", "two"], Arg(help="Foo.")] = "two"`, the
help text will be rendered as `Foo. Valid options: one, two. (Default: two)`

`arg_format` can be any of: A string, a callable, or a sequence of strings or callables.
Sequences of values will be joined together with an empty space, and **empty strings or `None`
will be ignored**.

The **purpose** of allowing sequences of individual segments is to ensure consistent
formatting when individual format options are not used. For example `"{help} {default}"`
would otherwise yield `Foo. ` or ` (Default: foo)` (i.e. trailing or leading spaces).
As such, where formatting may be variable (like with `default`), they should be split
into different segments.

Further, if simple format strings are not enough to ensure correct formatting, a segment
can alternatively be a callable (`Callable[[Arg], str | None]` or stricter). Again, if that
segment returns `None` or `""`, it will be omitted.

The following format string identifiers are included in the format context for each
segment: `help`, `default` (which in turn is rendered with `default_format`), `choices`, and `arg`.

An example of this might look like:

```python
from cappa import parse, HelpFormatter, Arg

class Command:
    foo: Annotated[str, Arg(help="Help text.", deprecated=True)] = "foo"

def deprecated(arg: Arg) -> str | None:
    if arg.deprecated:
        return "Deprecrated"
    return None

parse(Command, help_formatter=HelpFormatter(arg_format=("{default}", "{help}", deprecated))
```

Resulting in something like `(Default: foo) Help text. Deprecrated`.
