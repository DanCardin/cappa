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

## Aliases

Subcommands can declare alternate names that invoke the same command. This is
useful for short forms (`ls` for `list`), legacy spellings, and migration paths
when renaming a command.

Pass `aliases=` to `@cappa.command(...)`:

```python
import cappa
from dataclasses import dataclass

@cappa.command(aliases=["ls"])
@dataclass
class List:
    pass

@cappa.command(name="remove", aliases=["rm"])
@dataclass
class Remove:
    pass

@dataclass
class Tool:
    cmd: cappa.Subcommands[List | Remove]
```

With the above, `tool list`, `tool ls`, `tool remove`, and `tool rm` all work,
and `--help` displays both names per subcommand:

```
Subcommands
  list, ls
  remove, rm
```

### Hidden aliases

A bare string in `aliases=` produces a visible alias — it appears in `--help`
output and shell completion. Use `cappa.Alias(name, hidden=True)` to accept the
name without advertising it. This is handy for deprecated names you want to
keep working without showing in the UI:

```python
@cappa.command(
    aliases=[
        "ls",                              # visible
        cappa.Alias("dir", hidden=True),   # accepted, but absent from help
    ],
)
@dataclass
class List:
    pass
```

### Deprecated aliases

`cappa.Alias(name, deprecated=...)` emits a runtime warning to stderr when the
user invokes the command via that alias, while still dispatching to the
canonical command. Useful when you've renamed a subcommand but want to give
users a transition period:

```python
@cappa.command(
    name="remove",
    aliases=[
        cappa.Alias("rm", deprecated="use 'remove' instead"),
        cappa.Alias("delete", deprecated=True),  # default message
    ],
)
@dataclass
class Remove:
    pass
```

Invoking `tool rm` runs `Remove`, then prints:

```
Error: Command alias `rm` is deprecated: use 'remove' instead
```

`hidden` and `deprecated` compose — a hidden + deprecated alias is the typical
shape for an old name you want to keep alive but never show again.

### Imperative construction

When constructing commands manually (without the decorator), `aliases=` is a
keyword argument on `Command` itself:

```python
import cappa

cmd = cappa.Command(
    Tool,
    arguments=[
        cappa.Subcommand(
            field_name="cmd",
            options={
                "list": cappa.Command(List, name="list", aliases=["ls"]),
                "remove": cappa.Command(
                    Remove, name="remove", aliases=["rm"]
                ),
            },
        ),
    ],
)
```

The dict key in `Subcommand.options` remains the canonical name; aliases are
declared on each `Command` and resolved automatically.

### Collisions

Aliases must not collide with another subcommand's canonical name, with another
alias under the same parent, or with the command's own canonical name. Any of
these raises `ValueError` at command construction time so the conflict is
caught before the CLI ever runs.

```{eval-rst}
.. autoapiclass:: cappa.Subcommand
   :noindex:
```

```{eval-rst}
.. autoapiclass:: cappa.Alias
   :noindex:
```
