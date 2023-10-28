# Help Text Inference

Cappa tries to infer help text from a variety of sources, preferring them in
descending order of priority:

- An explicit `help=` argument
- A PEP-727 `Doc` annotation
- The class docstring argument description

If none of the above sources produce help text, no description will be rendered.

## Explicit `help=`

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

## PEP-727 `Doc` annotation

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

## Class Docstring Parsing

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
