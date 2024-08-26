# Subcommand

A subcommand class is just regular class capable of being a cappa
[Command](./command.md).

The primary relevant detail for actually attaching a subcommand to your command,
is that the field which captures the subcommand options must be annotated with
`Subcommand`.

As you'll have already seen throughout the documentation, before now.
Subcommands are expressed by annotating a union of subcommand options, and
annotating the union with `cappa.Subcommand`. I.e.

```{note}
If you want to explicitly control the name of a subcommand beyond the default,
you must annotate the command's class with `@cappa.command(name="the-name")`.
```

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Annotated
from cappa import Subcommand, Subcommands

@dataclass
class Command:
    # This
    subcommand: Subcommands[SubcmdOne | SubcmdTwo]

    # is shorthand for this
    subcommand2: Annotated[SubcmdOne | SubcmdTwo, Subcommand]

    # is shorthand for this
    subcommand3: Annotated[SubcmdOne | SubcmdTwo, Subcommand()]

@dataclass
class SubcmdOne:
    example: str

@dataclass
class SubcmdTwo:
    option: int
```

- You can use the `Subcommands[...]` shorthand to avoid the use of `Annotated`,
  in cases where you dont need to customize `Subcommand`'s constructor
  arguments.

- Annotation with `Subcommand` will instantiate it no arguments, getting the
  default behavior

- The above denotes a required subcommand with two options. To make it optional,
  you can additionally union the options with `None` and default the field to
  `None`.

- By default, name of the class (converted to dash-case) will be the CLI name
  for the subcommand option. E.x. `subcmd-one` and `subcmd-two`, from above. You
  can decorate each subcommand class with `@cappa.command(name='<x>')` to choose
  your own name.

```{eval-rst}
.. autoapiclass:: cappa.Subcommand
   :noindex:
```
