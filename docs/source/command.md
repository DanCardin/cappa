# Commands

A command can be as simple as a dataclass-like object, with no additional
annotations. Supported object-types include:

````{collapse} dataclasses
:open: 

```python
from cappa import parse

from dataclasses import dataclass

@dataclass
class Dataclass:
    name: str

value = parse(Dataclass)
assert isinstance(value, Dataclass)
```
````

````{collapse} Pydantic models
```python
from cappa import parse
from pydantic import BaseModel

class PydanticModel(BaseModel):
    name: str

value = parse(PydanticModel)
assert isinstance(value, PydanticModel)
```
````

````{collapse} Pydantic dataclasses
```python
from cappa import parse
from pydantic.dataclasses import dataclass as pydantic_dataclass

@pydantic_dataclass
class PydanticDataclass:
    name: str

value = parse(PydanticDataclass)
assert isinstance(value, PydanticDataclass)
```
````

````{collapse} Attrs classes
```python
from cappa import parse
from attr import define

@define
class AttrsClass:
    name: str

value = parse(AttrsClass)
assert isinstance(value, AttrsClass)
```
````

````{collapse} cattrs classes
```python
from cappa import parse
from attr import define

@define
class CAttrsClass:
    name: str

value = parse(CAttrsClass)
assert isinstance(value, CAttrsClass)
```
````

An undecorated dataclass-class will receive all the default [cappa.command](cappa.command)
behavior. In order to customize or change the default behavior, you would
begin by wrapping the class in the `@cappa.command` decorator like so:

```python
@cappa.command()
@dataclass
class Dataclass:
    name: str
```

```{note}
The wrapped class is directly returned from the decorator. So unlike `click`,
the resultant object can be directly used in the same way that you'd have been
able to do sans decorator.
```

```{note}
All arguments to [cappa.command](cappa.command) directly translate to [cappa.Command](cappa.Command)
attributes. When annotating an object with `@command()`, you are essentially pre-configuring
the generated [cappa.Command](cappa.Command) for that particular command.
```

## Subcommands

See [Subcommands](./subcommand.md) for details.

In short, any supported dataclass-like class that can be a top-level command is also
compatible with being a subcommand. The only difference is that subcommands
are attached to parent commands in a tree by way of having the parent define which
subcommands are available options.

```python
from cappa import Subcommands

@dataclass
class Command:
    subcommand: Subcommands[SubcmdOne | SubcmdTwo]
```

## `@command(name=...)` / `Command.name`

By default, the name of the command is inferred from the name of the containing
class, and converted to dash-case. For example `Example` would become `example`,
and `SomeLongName` would become `some-long-name`.

The `name` field can be used to override this behavior.

## `@command(help=...)` / `Command.help`

See [Help Text Inference](./help.md) for details.

Essentially this replaces any inferred (from docstring) **short** help text for the command.

## `@command(description=...)` / `Command.description`

See [Help Text Inference](./help.md) for details.

Essentially this replaces any inferred (from docstring) **extended** help text for the command.

## `@command(invoke=...)` / `Command.invoke`

See [Invoke](./invoke.md) documentation for more details.

Essentially this invokes a function upon a command/subcommand being selected during parsing,
corresponds to use of the `cappa.invoke` API rather than `cappa.parse`.

This API is roughly comparable to how `click` maps subcommands to functions.

## `@command(hidden=...)` / `Command.hidden`

Excludes the command in question from parent helptext generation. As such this
option is only relevant to subcommands.

## `@command(default_short=...)` / `Command.default_short`

By default unannotated arguments are considered to be ordered positional aruguments.

This option controls whether un-annotated arguments default to implying [Arg(short=True)](arg-short).

For example:

```python
@command(default_short=True)
@dataclass
class Foo:
    bar: int

# which is then called like:
# `foo -b 4`
```

## `@command(default_long=...)` / `Command.default_long`

By default unannotated arguments are considered to be ordered positional aruguments.

This option controls whether un-annotated arguments default to implying [Arg(long=True)](arg-long).

For example:

```python
@command(default_long=True)
@dataclass
class Foo:
    bar: int

# which is then called like:
# `foo --bar 4`
```

## `@command(default_negate_bool=...)` / `Command.default_negate_bool`

By default, boolean arguments receive a single `--flag` option that stores `True` when present.

This option controls whether un-annotated boolean arguments default to implying
[Arg(long="--flag/--no-flag")](arg-long), generating both a positive and negative
variant so the flag can be explicitly set to `False`.

For example:

```python
@command(default_negate_bool=True)
@dataclass
class Foo:
    verbose: bool = False

# which is then called like:
# `foo --verbose`      → verbose=True
# `foo --no-verbose`   → verbose=False
```

Non-boolean arguments are unaffected. Arguments with an explicit `long=` annotation
are also unaffected.

## `@command(prefix_chars=...)` / `Command.prefix_chars`

Defaults to `"-"`. The characters which mark a command line fragment as an option, rather than
a value (like `argparse`'s `prefix_chars`). For example, `prefix_chars="/"` gives
Windows-style options.

```{note}
The `argparse` backend passes `prefix_chars` through to `argparse.ArgumentParser` (including
  subcommand parsers), so the shape rules above are `argparse`'s own.
```

```python
@command(prefix_chars="/")
@dataclass
class Foo:
    verbose: Annotated[bool, Arg(short=True, long=True)] = False
    output: Annotated[str, Arg(short=True)] = "out"

# which is then called like:
# `foo /v`               → verbose=True
# `foo //verbose`        → verbose=True
# `foo /o file`          → output="file"
# `foo /h`, `foo //help` → help
```

`prefix_chars="-/"` accepts options starting with either character.

### **Option shape**

Each character in `prefix_chars` is treated individually, therefore there are no multi-character
prefixes.

A **short** option starts with a single prefix character (`-v`, `/v`). A **long** option
starts with a **doubled** prefix character (`--verbose`, `//verbose`). Note the doubled
characters can differ (`/-verbose` is "long" when `prefix_chars="-/"`), which matches `argparse`.

A lone prefix character (`-`, `/`) is always a value, not an option. This keeps `-` usable as
a stdin/stdout placeholder.

The `--` terminator is **always** the literal `--`, regardless of `prefix_chars`.

### **Name inference**

Inferred names use the **first** character of `prefix_chars="-/"`: `short=True` yields `-v`
and `long=True` yields `--verbose`. The same applies to the negated form
generated by `default_negate_bool`. Therefore in order to get the other allowed prefix chars
for an `Arg`, you must (currently) explicitly supply the allowed options rather than using `True`.

```{note}
There is a slight quirk with `/` as a prefix char, in that `short="-a/-b"` can be used as shorthand
for allowing multiple aliases. This become ambiguous when `/` is an available prefix character, so this
shorthand is disabled in that case and `["/a", "/b"] must instead be supplied.
```

### **Inheritance**

`prefix_chars` is **not** inherited by subcommands. Each command tokenizes its own portion of
  the command line, so a subcommand which should use `/` options must set it itself.

Destructured arguments use the **outer** command's `prefix_chars`, not the destructured class's,
since the outer command is the one which parses them.

[Propagated arguments](arg-propagate) keep the names given to them by the command which
  declares them. They are not renamed for a child command, so propagating through a subcommand
  with a different `prefix_chars` produces options the child cannot spell. Keep the setting
  consistent across commands which share propagated arguments.

### **Parsing**

There is no per-`Arg` override. Tokenization happens before the parser knows which argument a
fragment belongs to.

A fragment which **exactly matches** a known option is never split into concatenated short
options. Otherwise `/verbose` would be read as `/v` followed by `erbose` whenever `/v` also
exists. This applies to the default `-` prefix as well (e.x. a declared `-verbose`).

Relatedly, concatenated short options use the prefix of the fragment they came from, e.x.
`+ab` is `+a +b`. Under `prefix_chars="+-"` the options are *declared* as `+a`/`+b`, so `-ab`
would not match them.

```{note}
Note, **values which begin with a prefix character are parsed as options.** The most notable case
is `prefix_chars="/"`, where an absolute path like `/tmp/file` is treated as an (unknown)
option, and produces an error.

The ways around that are the same as for `-`: `/o=/tmp/file`, placing the value after `--`,
or [`Arg.allow_prefixed_values`](arg-allow-prefixed-values).
```

A value starting with a character that is **not** in `prefix_chars` is never
ambiguous. With `prefix_chars="/"`, `-5` or `-x` are plain values. [`Arg.allow_prefixed_values`](arg-allow-prefixed-values)
follows `prefix_chars`: it allows a value to start with any of them.

## `@command(deprecated=...)` / `Command.deprecated`

This generates a warning if the command in question is used at runtime.

If `True` is supplied, a default deprecation message is generated. Alternatively
it accepts the string message that should be emitted.

## API

```{eval-rst}
.. autoapiclass:: cappa.Command
   :noindex:
```
