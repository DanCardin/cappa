# Annotations

Annotations perform two functions:

- Inferring specific `Arg`-level options, depending on the specific annotation,
  most of which control parsing behavior for that argument.

- Mapping the raw parsed arguments into the specified output types.

In any case where the "supported" set of behaviors given by the inference system
does not produce the obvious result, feel free to submit a bug report. The
intent is that it should feel natural for all supportable cases. For any cases
where it does not make sense to build in specific behavior for a type (for
example, third-party library types), you can instead use the correct annotation
while providing the `parse`, or other [arguments](./arg.md).

```{note}
Use of `Annotated` throughout the examples and docs is fairly pervasive. When using
versions of python below 3.9, `Annotated` is not included in the `typing` module.

Instead, you can install [typing_extensions](https://pypi.org/project/typing_extensions/),
which backports typing objects to earlier versions of python.
```

```{note}
Similarly, use of `|` for `Union`s is universally preferred in the docs. When using
versions of python below 3.10, you may need to use `from __future__ import annotations`
at the top of your file in order for the annotations to be ignored by the python runtime.
```

## Positional vs Option

Below, any reference to "positional" implies, a field which does not set
`short=...` or `long=...`. This includes any fields with no explicit `Arg`
instance at all.

- `foo: str`
- `foo: Annotated[str, Arg()]`

Whereas an "option" is a field which **does** set `short=...` or `long=...`.

- `foo: Annotated[str, Arg(short=True)]`
- `foo: Annotated[str, Arg(long=True)]`
- `foo: Annotated[str, Arg(short="-f", long=True)]`

This is an important distinction to note, because the inference system makes
difference decisions, depending on whether a given field is positional or not.

## `Arg` Inference

Note that in all cases below, any individual inferred value can be overridden in
any case where the default inference is not what you're looking for!

### Bool

In most other cases, an un-annotated field like `foo: str` is assumed to be a
positional argument.

By contrast a `foo: bool` is assumed to be an optional flag. This is because
bools corresponding to flags represent the much more common case.

By default a `foo: bool` implies
`foo: Annotated[bool, Arg(long=True, num_args=0, action=ArgAction.store_true, required=False)]`.

- If you also want to enable a "short" version of the flag, you can set
  `Arg(short=True)`.

- If you include a `--no-<name>` long name variant like
  `Arg(long=['--foo', '--no-foo'])`, the `--no-foo` variant will be inferred as
  `ArgAction.store_false`.

- If a vanilla bool annotation (without an inverted variant) is combined with a
  default value of `True`, then the action is inverted to
  `ArgAction.store_false`.

  This is because `foo: bool = True` could never result in a `False` value, if
  supplying `--foo` at the command line also stored `True`.

See [Arg.short](cappa.Arg.short) and [Arg.long](cappa.Arg.long) for more details
on customization of the specific flag names.

```{note}
If (for whatever reason) you require a positional argument interpreted as a bool,
you can explicitly set `Arg(long=None, action=ArgAction.set, num_args=1)`
```

### Sequence Types

Annotations like `list[...]`, `set[...]`, `tuple[...]`, etc are what we call
"sequence types".

- In the case of a positional argument, a sequence type annotation implies
  `Arg(..., num_args=length_bound)`.

  For "bounded" length sequences (i.e. tuples like `tuple[int]`,
  `tuple[int, int]`, `tuple[int, int, int]`, etc), `length_bound` corresponds to
  the indicated length of the sequence.

  For "unbounded" length sequences (i.e. list, set, and unbounded tuples:
  `tuple[int, ...]`), `length_bound=-1`, i.e. the argument will consume an
  unbounded number of positional arguments (`prog foo bar baz ...`).

  ```python
  @dataclass
  class Prog:
      foo: list[str]

  prog = cappa.parse(Prog, argv=['foo', 'bar', 'baz'])
  assert prog == Prog(foo=['foo', 'bar', 'baz'])
  ```

- In the case of option arguments, a sequence type annotation implies
  `Arg(..., action=ArgAction.append)`. That is, it allows multiple uses of the
  option to accumulate the values into a sequence.

  ```python
  @dataclass
  class Prog:
      foo: Annotated[list[str], Arg(short=True)]

  prog = cappa.parse(Prog, argv=['-f', 'foo', '-f', 'bar', '-f', 'baz'])
  assert prog == Prog(foo=['foo', 'bar', 'baz'])
  ```

  ```{note}
  You can specify `Annotated[list[str], Arg(short=True, num_args=n)]` where
  `n` would yield a sequence (`-1` or > 1). In such a case, `action` would instead
  be inferred as `ArgAction.set`.
  ```

See [Argument](./arg.md) for more details on the difference between
`ArgAction.append` and `num_args=-1`.

### `| None` or `Optional[...]`

Either form of `Optional`-type annotation implies
`Arg(required=False, default=None)`.

### Unions

Unions don't currently apply any specific inference behavior, but they do come
with some restrictions.

- Unioning "scalar" and "sequence" types will raise an `ValueError`.

  For example, `int | list[str]`. `list[str]` wants to produce a list, whereas
  `int` wants to produce a single value, and it's unclear how the parser ought
  to react to such an annotation.

- Unioning types which would produce different inferred `num_args` values will
  raise a `ValueError`.

  For example, `foo: tuple[str, str] | list[str]`. `int` produces `num_args=2`
  and `list[str]` will produce `num_args=-1`, which are incompatible.

### Literals and Enums

Any form of explicit "choice", like `Literal["one", "two"]`,
`Literal["one"] | Literal["two"]`, `Enum` implies `Arg(choices=[...])`.

In case of literals, it is obviously the list of all unioned literals. In case
of `Enum` subclasses, all variants are given as the set of choices.

`choices` represents a parser-level evaluation of the CLI input value versus the
available choices, resulting in a parse error in the event the value does not
match.

### Subcommands

Unions among subcommand options `Subcommands[One | Two | Three]` are how
subcommand options are expressed. See [Command](./command.md) docs for more
details.

The order of the unioned subcommand options does not have any effect because
each subcommand has a unambiguous name.

## Mapping Inference

Mapping inference is a sort of subset of `Arg`-settings inference, in that it
effectively uses the annotated type to set `Arg(parse=...)` in a way that maps
the raw values coming out of a sucessful CLI parse into the annotated types.

As such you can again, opt out of the "Mapping inference" entirely, by supplying
your own `parse` function.

```{note}
Mapping inference is built up out of component functions defined in `cappa.parse`,
such as `parse_list`, which know how to translate `list[int]` and a source list of raw
parser strings into a list of ints.

These functions can/could be utilized in your own custom `parse` functions.
```

### Basic Scalar Types

Any "basic" data type (like `int`, `float`, `str`) are supported and coerced to
directly, by calling their constructor.

This also applies even to "complex" ones who's constructor accepts a string and
returns the type (such as `pathlib.Path`, or `decimal.Decimal`).

Note this also applies to `Enum`s, who's raw values by map-time should be
guaranteed to be compatible with the Enum's variants.

### `date`/`datetime`/`time`

Both types are directly supported through inference, by calling the `fromisoformat`
method on each type.

```{note}
The set of supported input formats are
[python version specific](https://docs.python.org/3/library/datetime.html#datetime.date.fromisoformat).
```

To support more general input formats, you should instead supply a function to
`Arg(parse=...)` which accepts a string and returns the given type.

### Union (and Optional)

Unions are handled by recursively processing the set of unioned inner types
using whatever logic applies to that type. The primary important point here, is
that the order of the set of unioned types **can** matter, but generally
shouldnt.

The unioned types are sorted and processed in descending order from:

- "other" types/None
- float
- int
- bool/str

This specific order order is given to prioritize types which are less likely to
succeed parsing when given incorrect input.

`bool` and `str` are notable in that will always "succeed" (in that given any
input they will produce an output) and not fail. As such it **may** not make
much sense to union those types together without an explicit `parse`.

Therefore, when unioning "other"-type types, it **may** be important to consider
the order of the unioned types, if parsing for one or the other type would
"succeed" incorrectly. In such cases, `parse` may be appropriate.

```{note}
It's possible for more complex value mapping to happen automatically, if the
input types have distinct "success criteria". This amounts to something akin to
a discriminated union.

For example, take the annotation `tuple[Literal["foo"], str] | tuple[Literal["bar"], int]`.
Supplying `foo bar` as the input value should produce `("foo", "bar")`, whereas
`bar 4` should produce `("bar", 4)`.
```

### List/Tuple/Set

`list[...]`, `tuple[...]`, `set[...]` all will coerce the parsed sequences of
values into their corresponding type. The inner type will be mapped for each
item in the sequence.

### `typing.BinaryIO`/`typing.TextIO`

[BinaryIO](typing.BinaryIO) and [TextIO](typing.TextIO) are used to produce an
open file handle to the file path given by the CLI input for that argument.

This can be thought of as equivlent to `open("foo.py")`, given some
`cli --foo foo.py`, which is roughly equivalent to the
[FileType](https://docs.python.org/3/library/argparse.html#argparse.FileType)
feature from `argparse`.

```python
@dataclass
class Args:
    foo: typing.BinaryIO


args = cappa.parse(Args)
with args.foo:
    print(args.foo.read())
```

```{note}
The supported types do not map to concrete, instantiatable types. This is
important, because neither of these types would otherwise be valid type
annotations in the context of cappa's other inference rules.

It's also important, because there are no concrete types which correspond
to the underlying types returned by `open()`, which would allow the distinction
between binary and text content.
```

#### Controlling `open(...)` options like `mode="w"`

An un-`Annotated` IO type translates to `open(<cli value>)` with no additional
arguments, with the exception that `BinaryIO` infers `mode='b'`.

In order to directly customize arguments like `mode`, `buffering`, `encoding`,
and `errors`, a [FileMode](cappa.FileMode) must be annotated on the input
argument.

```python
import dataclasses
import typing
import cappa

@dataclasses.dataclass
class Args:
    foo: typing.Annotated[typing.BinaryIO, cappa.FileMode(mode='wb', encoding='utf-8')]
    bar: typing.Annotated[typing.BinaryIO, cappa.Arg(short=True), cappa.FileMode(mode='wb')]
```

As shown, [FileMode](cappa.FileMode) is annotated much like a [Arg](cappa.Arg),
and can be used alongside one depending on the details of the argument in
question.
