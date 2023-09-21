# Subcommand

A subcommand target, is just regular class capable of being a cappa
[Command](./command.md).

The primary relevant detail for actually attaching a subcommand to your command,
is that the field which captures the subcommand options must be annotated with
`Subcommand`.

As you'll have already seen throughout the documentation, before now.
Subcommands are expressed by annotating a union of subcommand options, and
annotating the union with `cappa.Subcommand`. I.e.

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Annotated
from cappa import Subcommand

@dataclass
class Command:
    subcommand: Annotated[SubcmdOne | SubcmdTwo, Subcommand]

@dataclass
class SubcmdOne:
    ...

@dataclass
class SubcmdTwo:
    ...
```

- The above denotes a required subcommand with two options. To make it optional,
  you can additionally union with `None` and default it to `None`

- The annotation is to `Subcommand` the class, not an instance. You can
  optionally supply the class, and it will be instantiated with no arguments.

- The name of the class converted to dash-case (ex. above `subcmd-one` and
  `subcmd-two`), is the default name each subcommand. You can decorate each
  subcommand class with `@cappa.command(name='<x>')` to choose your own name.

```{eval-rst}
.. autoapimodule:: cappa
   :members: Subcommand
   :noindex:
```
