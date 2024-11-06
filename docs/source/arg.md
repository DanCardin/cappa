# Arguments

Similar to commands, use of cappa-specific argument annotations are "only"
required when the default behavior is not what you want. A completely
un-annotated dataclass like

```python
@dataclass
class Example:
    name: str
```

is perfectly valid. However, a CLI of any real complexity **will** need to use
the `Arg` annotation.

By default:

- Each class member is inferred to be a positional argument
- Its name is the dash-case version of the class member name
- Its value is coerced to the annotated type
- Its help text is inferred from various natural sources (See
  [Help Text Inference](./help.md) for details)

However, by using `Arg`, with syntax like
`name: Annotated[str, cappa.Arg(...)]`, you can customize the behavior of the
field.

- `short=True` (equivalent to `short='-n'` for this example) turns the option
  from a positional argument into a flag.
- `long` works the same way as short (and can be used together), but for `--`
  flags, like `--name`.
- `count=True` counts the number of flag instance. Frequently used for `-v`,
  `-vv`, `-vvv` verbosity handling.
- `help='...'` allows customizing the help text outside the docstring.
- `parse=<callable>` allows parsing of more complex input values the cannot be
  handled through the type annotation system directly.

```{note}
See the [annotation docs](./annotation.md) for more details on how annotations
can be used and are interpreted to handle different kinds of CLI input.
```

```{eval-rst}
.. autoapiclass:: cappa.Arg
   :noindex:
```

(arg-action)=
## `Arg.action`

Obliquely referenced through other `Arg` options like `count`, every `Arg` has a
corresponding "action". The action is automatically inferred, most of the time,
based on other options (i.e. `count`), the annotated type (i.e. `bool` ->
`ArgAction.store_true/ArgAction.store_false`, `list` -> `ArgAction.append`), etc.

However the inferred action can always be directly set, in order to override the
default inferred behavior.

### Custom Actions

```{note}
This feature is currently experimental, in particular because the parser state
available to either backend's callable is radically different. However, for an
action callable which accepts no arguments, the behavior is unlikely to change.
```

In addition to one of the literal `ArgAction` variants, the provided action can
be given as an arbitrary callable.

The callable will be called as the parser "action" in response to parsing that
argument.

```{note}
Custom actions may interfere with general inference features, depending on what you're
doing (given that you're taking over the parser's duty of determining how the
code ought to handle the argument in question).

As such, you may need to specify options like `num_args`, where you wouldn't have otherwise
needed to.
```

Similarly to the [invoke](./invoke.md) system, you can use the type system to
automatically inject objects of supported types from the parse context into the
function in question. The return value of the function will be used as the
result of parsing that particular argument.

The set of available objects to inject include:

- [Command](cappa.Command): The command currently being parsed (a relevant piece
  of context when using subcommands)
- [Arg](cappa.Arg): The argument being parsed.
- [Value](cappa.parser.Value): The raw input value parsed in the context of the
  argument. Depending on other settings, this may be a list (when num_args > 1),
  or a raw value otherwise.
- [RawOption](cappa.parser.RawOption): In the event the value in question
  corresponds to an option value, the representation of that option from the
  original input.

The above set of objects is of potentially limited value. More parser state will
likely be exposed through this interface in the future. If you think some specific
bit of parser state is missing and could be useful to you, please raise an issue!

For example:

```python
def example():
    return 'foo!'

def example(arg: Arg):
    return 'foo!'

def example2(value: Value):
    return value.value[1:]


@dataclass
class Example:
    ex1: Annotated[str, cappa.Arg(action=example)
    ex2: Annotated[str, cappa.Arg(action=example2)
    ex3: Annotated[str, cappa.Arg(action=example3)
```

```{eval-rst}
.. autoapiclass:: cappa.ArgAction
   :noindex:
```

```{warning}
`ArgAction.append` and `num_args=-1` can be potentially confused, in that they can both
produce list/sequence types as outputs. They can be used in conjunction or separately,
but they are not the same!

Given some example option `--foo`:

`ArgAction` generally, affects the way the parser maps input CLI values to a given field
overall. As such `ArgAction.append` causes the field-level value to be a sequence, and
for multiple instances of `--foo` to accumulate into a list. e.x. `--foo 1 --foo 2` -> `[1, 2]`.

`num_args` instead, affects the number of values that a single instance of `--foo` will
consume before stopping. e.x. `--foo 1 2` -> `[1, 2]`.

From an input perspective, the above examples show how they present differently at the CLI
interface, requiring different inputs to successfully parse. From an output perspective, the
table below shows how their parsed output will end up looking when mapped to real values.

| action | num_args | result |
| ------ | -------- | ------ |
| set    | 1        | 1      |
| set    | -1       | [1]    |
| append | 1        | [1]    |
| append | -1       | [[1]]  |
```

## `Arg.num_args`

`num_args` controls the number of arguments that the parser will consume in
order to fulfill a specific field. `num_args=1` is the default behavior,
meaning only one argument/value will be consumed for that field. This yields a
scalar-type value.

`num_args=3` would therefore mean that exactly 3 values would be required,
resulting in a sequence-type output, rather than a scalar one.

`num_args=-1` can be used to indicate that 0 or more (i.e. unbounded number of)
arguments will be consumed, similarly resulting in a sequence-type output (even
in the zero case).

```{note}
Generally `num_args` will be automatically inferred by your type annotation. For example,
`tuple[int, int, int]` implies `num_args=3`.

However, an explicitly provided value is always preferred to the inferred value.
See [annotations](./annotation.md) for more details.
```

## `Arg.default`

Controls the default argument value at the CLI level. Generally, you can avoid
direct use of cappa's default by simply using the source class' native default
mechanism. (i.e. `foo: int = 0` or `foo: int = field(default=0)` for
dataclasses).

However it can be convenient to use cappa's default because it does not affect
the optionality of the field in question in the resultant class constructor.

```{note}
The `default` value is not parsed by `parse`. That is to say, if no value is
selected at the CLI and the default value is used instead, it will not be
coerced into the annotated type automatically.

The reason for this is twofold:

1. Typechecking should already emit an error when the given default is of the incorrect type.
2. This interacts poorly with types who's constructor does not accept an instance
   of the given type as an input argument. For example, `foo: Foo = Foo('')`
   would infer `parse=Foo` and attempt to pass `Foo(Foo(''))` during parsing.
```

### Environment Variable Fallback

You can also use the default field to supply supported kinds of
default-value-getting behaviors.

`Env` is one such example, where with
`Arg(..., default=Env("FOO", default='default value'))`, cappa will attempt to
look up the environment variable `FOO` for the default value, if there was no
supplied value at the CLI level.

```{eval-rst}
.. autoapiclass:: cappa.Env
   :noindex:
```

(arg-group)=
## `Arg.group`: Groups (and Mutual Exclusion)

`Arg(group=...)` can be used to customize the way arguments/options are grouped
together and interpreted.

The `group` argument can be any of:

- `str`: A string that indicates a custom group. This only affects help text output,
  by placing any `Arg`s with that group string under a common heading.

  ```python
  class Example:
      arg1: Annotated[str, Arg(group='Special')]
      arg2: Annotated[str, Arg(group='Special')]
  ```

- `tuple[int, str]`: This additionally provides an `int` which is considered when
  determining the `order` of group output.

  ```python
  class Example:
      arg1: Annotated[str, Arg(group=(4, 'Special'))]
      arg2: Annotated[str, Arg(group=(4, 'Special'))]
  ```

- [Group](Group): Instances of `Group` are the normalized form of the above two shorthand
  options (which are ultimately coerced into `Group`s).

  [Group](Group) additionally has an `exclusive: bool` option, which can be used to indicate
  that options within a group are mutually exclusive to one other.

  ```{note}
  Both `order` and `exclusive` options on `Group` are expected (and validated)
  to be identical across all options sharing that group string.
  ```

  ```python
  class Example:
      arg1: Annotated[str, Arg(group=Group('Special', exclusive=True))]
      arg2: Annotated[str, Arg(group=Group('Special', exclusive=True))]
  ```

  In this case, `example --arg1 foo --arg2` would generate an error like:

  ```
  Argument 'arg1' is not allowed with argument 'arg2'
  ```

(exclusive-group-syntax)=

### Dedicated Mutual Exclusion Syntax

A potentially common use of mutually exclusive arguments would be two distinct
CLI-level arguments, which ultimately are different ways of configuring a specific
code-level field.

In such cases, two (or more) `cappa.Arg`s can be annotated on a single class field.
This **implies** a mutually exclusive group automatically, defaulting to the name
of the field ("Verbose" in this case) as the group name. For example:

```python
@dataclass
class Example:
    verbose: Annotated[
        int,
        cappa.Arg(short="-v", action=cappa.ArgAction.count),
        cappa.Arg(long="--verbosity"),
    ] = 0
```

- `example -vvv` would yield: `verbose=3`
- `example --verbosity 4` would yield: `verbose=4`
- `example -vvv --verbosity 4` would yield the error: `Argument '--verbosity'
is not allowed with argument '-v'`

```{note}
An explicit `group=` can still be used in concert with the above syntax to control
the `order` and name of the resultant group.
```

## `Arg.parse`

`Arg.parse` can be used to provide **specific** instruction to cappa as to how to
handle the raw value given from the CLI parser backend.

In _general_, this argument shouldn't need to be specified because the annotated
type will generally _imply_ how that particular value ought to be parsed, especially
for built in python types.

However, there will inevitably be cases where the type itself is not enough to infer
the specific parsing required. Take for example:

```python
from datetime import date

@dataclass
class Example:
    iso_date: date
    american_date: Annotated[date, cappa.Arg(parse=lambda date_str: date.strptime('%d/%m/%y'))]
```

Cappa's default date parsing assumes an input isoformat string. However you might instead
want a specific alternate parsing behavior; and `parse=` is how that is achieved.

Further, this is likely more useful for parsing any custom classes which dont have simple,
single-string-input constructor arguments.

```{note}
Note cappa itself contains a number of component `parse_*` functions inside the `parse`
module, which can be used in combination with your own custom `parse` functions.
```

(parsing-json)=
### Parsing JSON

Another example of a potentially useful parsing concept could be to parse json string input.
For example:

```python
import json
from dataclasses import dataclass
from typing import Annotated

import cappa

@dataclass
class Example:
    todo: Annotated[dict[str, int], cappa.Arg(parse=json.loads)]

todo = cappa.parse(Todo)
print(todo)
```

Natively (at present), cappa doesn't have any specific `dict` type inference because it's
ambiguous what CLI input shape that ought to map to. However, by combining that with
a dedicated `parse=json.loads` annotation, `example.py '{"foo": "bar"}'` now yields
`Example({'foo': 'bar'})`.

(composing-parsers)=
### Composing Multiple Parsers

`Arg.parse` accepts **either** a single parser function, like above, or a sequence of parsers
which will be called...in sequence. The return value of earlier parsers in the chain will be
routed into the input of later parsers.

```python
import json
from dataclasses import dataclass
from typing import Annotated

import cappa

def get_key(value: dict[str, str]) -> str:
    return value.get("todo", "")

@dataclass
class Example:
    todo: Annotated[str, cappa.Arg(parse=[json.loads, get_key])]

todo = cappa.parse(Todo)
print(todo)
```

(unpack-arguments)=
### `unpack_arguments`: Invoking constructors with `*` and `**` operators

In some cases, you might want to construct objects that have required keyword arguments (pydantic
models!) or otherwise who's constructors do not accept the single argument that would typically be
provided to single CLI fields' parser. This is the use case for [cappa.unpack_arguments](cappa.unpack_arguments).

Cappa will unpack the arguments based on the incoming type of data (e.g. sequence vs mapping).

```{note}
(Arg.destructure)[#argument-destructuring] is a **similar** feature, in that it allows one to compose
complex types into the CLI structure; but it in essentially opposite uses. `unpack_arguments` produces
a complex type from a single CLI argument, whereas a "destructured" argument composes together multiple
CLI arguments into one object without requiring a separate command.
```

#### *args Unpacking
Sequence unpacking (`*`) can be used to provide values to constructors that accept multiple arguments
positionally. For example:

```python
from dataclasses import dataclass
from typing import Annotated
from cappa import unpack_arguments, Arg, parse

@dataclass
class Point:
    x: int
    y: int


@dataclass
class CLI:
    point: Annotated[Point, Arg(num_args=2, parse=unpack_arguments)]

print(parse(CLI))
```

```bash
$ cli.py 1, 2
CLI(Point(1, 2))
```

**Without** `unpack_arguments`, the `Point(...)` constructor call would have
been handed `[1, 2]`. Essentially the above is roughly equivalent to

```python
class Point:
    ...
    @classmethod
    def from_list(cls, value: list[int]):
        return cls(*value)

...
class CLI:
    point: Annotated[Point, Arg(num_args=2, parse=Point.from_list)]
```

#### **kwargs Unpacking

Mapping unpacking (`**`) can be used for constructors which accept multiple arguments
by keyword. For example, **Pydantic** classes' constructors **require** keyword-only
arguments. This poses a challenge to a single CLI argument representing that constructor
value. One way around this could be accepting a JSON string, parsing the string as JSON,
and then unpacking the result into the constructor, effectively combining [Parsing JSON](#parsing-json)
and [Composing Multiple Parsers](#composing-parsers).

```python
from pydantic import BaseModel
from typing import Annotated
from cappa import unpack_arguments, Arg, parse

class Point(BaseModel:
    x: int
    y: int


@dataclass
class CLI:
    point: Annotated[Point, Arg(parse=[json.loads, unpack_arguments])]

print(parse(CLI))
```

```bash
$ cli.py '{"x": 1, "y": 2}'
CLI(Point(1, 2))
```

Similarly, you could imagine swapping `json.loads` for some alternate parser which accepted/parsed
`x=1,y=2` or other input formats.

### Parse Dependencies

Parse functions can are provided the same dependency injection system given by `invoke` and
[actions](#arg-action). Thus, by accepting an additional argument to the parser annotated with
a supported type annotation, they'll be provided that runtime value automatically.

This enables user-defined parsers that have the same amount of information that built-in parsers
have when making decisions, namely the type information.

Currently supported injectable values include:

* [TypeView](https://github.com/litestar-org/type-lens/blob/main/type_lens/type_view.py)

```python
from cappa.type_view import TypeView

def parse(value, type_view: TypeView):
    value = json.loads(value)
    if type_view.is_mapping:
        return value
    raise ValueError("Requires a JSON mapping, string input!")

class CLI:
    arg: Annotated[int, Arg(parse=parse)]
```

```{note}
More injectable dependencies **could** be supported. In particular the `Arg` instance comes to mind,
it's just not immediately obvious what that would be. File an issue if you have a usecase!
```

## `Arg.has_value`

`Arg(has_value=True/False)` can be used to explicitly control whether the argument in question
corresponds to a destination-type attribute as a value.

For example the `Arg` that produces the `--help` option has a dedicated action which produces
help text, and as such has a `has_value=False`.

While there may not be much point in manually setting this attribute to `True` (because it will default
to `True` in most cases), you **could** conceivably manually combine `has_value=False` and a
custom [action](#action), to avoid cappa trying to map your `Arg` back to a specific attribute.

(argument-destructuring)=
## `Arg.destructured`/`Arg.destructure()`

**Generally** a single class/type corresponds to a command, and that type's attributes correspond to
the arguments/options for that command.

The [exclusive group syntax](#exclusive-group-syntax) is one counter example, where a single
class attribute maps to more than one CLI argument.

"Destructured" arguments are essentially the inverse, in that they allow multiple attributes
(and thus CLI arguments) to be mapped back to a single command's class attribute.

```python
from __future__ import annotations
from typing import Annotated

@dataclass
class Args:
    sub_object: Annotated[SubObject, Arg.destructured()]


@dataclass
class SubObject:
    arg1: Annotated[str, Arg(long=True)]
    arg2: Annotated[int, Arg(long=True)]
```

This essentially fans out the `--arg1=foo --arg2=2` CLI arguments up into the parent `Args` command,
while ultimately mapping the resultant values back into the expected output structure of:
`Args(sub_object=SubObject(arg1='foo', arg2=2))`.

This concept has a couple of practical uses:

- Code/argument reuse: In the above example `SubObject` can now be shared between multiple subcommands
  to provide the same set of arguments in different places **without** requiring subclassing.

- Logical grouping/organization: This allows grouping of logically related fields in the **python**
  code without affecting how those arguments are represented in the CLI shape.

```{note}
Currently `Arg.destructure()` only works with **singular concrete** type annotations. That is,
in the above example `Annotated[SubObject, Arg.destructured()]`;
whereas it will raise a `ValueError` if given `SubObject | None` or other more exotic annotations.

Principally, `Annotated[SubObject | None, Arg.destructured()]` **could** make sense to imply that all
child options are therefore optional, or that if any child attributes are missing, then that implies
`sub_object=None` at the top level. However both of these are mechanically much more complex than the
feature, as it exists today.

Additionally, this feature only works with the native backend. This **probably** has a workable
solution for argparse, so file an issue if this affects you!
```

```{note}
(unpack_arguments)[#unpack-arguments] is a **similar** feature, in that it allows one to compose
complex types into the CLI structure; but it in essentially opposite uses. `unpack_arguments` produces
a complex type from a single CLI argument, whereas a "destructured" argument composes together multiple
CLI arguments into one object without requiring a separate command.
```

## `Arg.propagate`

Argument propagation is a way of making higher-level arguments available during the parsing of child
subcommands. When an argument is marked as `Arg(propagate=True)`, access to that argument will
be made available in all **child** subcommands, while still recording the value itself to the
object on which it was defined.

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Annotated
import cappa

@dataclass
class Main:
    file: Annotated[str, cappa.Arg(long=True, propagate=True)]
    subcommand: cappa.Subcommands[One | Two | None] = None

@dataclass
class One:
    ...

@dataclass
class Two:
    subcommand: cappa.Subcommands[Nested | None] = None

@dataclass
class Nested:
    ...

print(cappa.parse(Main))
```

Given the above example, all of the following would be valid, and produce `Main(file='config.txt', ...)`:

- `main.py --file config.txt`
- `main.py one --file config.txt`
- `main.py two --file config.txt`
- `main.py two nested --file config.txt`


If defined on a top-level command object (like above), that argument will effectively
be available globally within the CLI, again while actually propagating the value
back to the place at which it was defined.

However if the propagated argument is **not** defined at the top-level, it will
not propagate "upwards" to parent commands; only downward to child subcommands.

```{note}
`Arg.propagate` is not currently enabled/allowed for positional arguments (file an issue if this
is a problem for you!) largely because it's not clear that the feature makes any sense except
on (particularly optional) options.

`Arg.propagate` is not implemented in the `argparse` backend.
```

### Propagated Arg Help

By default propagated arguments are added to child subcommand's help as though the argument
was defined like any other argument.

If you want propagated arguments categorically separated from normal arguments, you can
assign them a distinct [group](#arg-group), which will cause them to be displayed separately.

For example:
```python
group = cappa.Group(name="Global", section=1)

@dataclass
class Command:
    other1: Annotated[int, cappa.Arg(long=True)] = 1
    other2: Annotated[int, cappa.Arg(long=True)] = 1
    foo: Annotated[int, cappa.Arg(long=True, propagate=True, group=group)] = 1
    bar: Annotated[str, cappa.Arg(long=True, propagate=True, group=group)] = 1
```

Would yield:

```
  Options
    [--other1 OTHER1]          (Default: 1)
    [--other2 OTHER2]          (Default: 1)

  Global
    [--foo FOO]                (Default: 1)
    [--bar BAR]                (Default: 1)
```

Note, this is no different from use of `Arg.group` in any other context, except in that
the argument only exists at the declaration point, so any grouping configuration will
also propagate down into the way child commands render those arguments as well.
