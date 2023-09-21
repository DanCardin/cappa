# Annotations

Annotations are use to control the output type of each argument, and infer type
cast/parsing logic on behalf of the programmer.

In any case where the "supported" set of behaviors given by the inference system
does not produce the obvious result, feel free to submit a bug report. The
intent is that it should feel natural for all supportable cases. For any cases
where it does not make sense to build in specific behavior for a type (for
example, third-party library types), you can instead use the correct annotation
while providing the `parse` [Argument](./arg.md) argument.

```{note}
Use of `Annotated` throughout the examples and docs is fairly pervasive. When using
versions of python below 3.9, `Annotated` is not included in the `typing` module.

Instead, you can install [typing_extensions](https://pypi.org/project/typing_extensions/),
which backports typing objects to earlier versions of python.
```

## Basic Data Types

Any "basic" data type (like `int`, `float`, `str`) are supported and coerced to
directly.

This also applies even to "complex" ones who's constructor accepts a string and
returns the type (such as `pathlib.Path`, or `decimal.Decimal`)

## Union (and Optional)

```{note}
`Optional` is just shorthand for `Union[T, None]`, so it falls under `Union` handling.

The **only** additional behavior is that unioning with `None` automatically makes the
flag optional (i.e. `required=False`).
```

Unions are handled by recursively processing the set of unioned types using the
same logic. The primary important point here, is that the order of the set of
unioned types **can** matter, but generally shouldnt.

The unioned types are sorted (and thus handled) in descending order from:

- "other" types/None
- float
- int
- bool/str

This specific order order is given to prioritize types which are less likely to
succeed parsing when given incorrect input. Whereas, for example, `bool` or
`str` will always "succeed" (in that given any input they will produce an
output).

Therefore, when unioning "other"-type types, it **may** be important to consider
the order of the unioned types, if parsing for one or the other type would
"succeed" incorrectly. In such cases, `parse` may be appropriate.

```{note}
Unions are how selections among subcommand options are expressed. See
[Command](./command.md) docs for more details.

The order of the unioned subcommand options removes order ambiguity, because
each subcommand has a unambiguous name.
```

## List

Lists change the "action" of the option to "append", which causes the parser to
allow an arbitrary number of values for that option.

For a specific number of values, you should instead use tuples

Lists coerce to whatever the inner type is.

## Tuple

Tuples change the number of args parsed by the option to the number items in the
tuple.

In the event something like `tuple[T, ...]` is encountered, type checkers
interpret this to mean unbounded size tuple of type T. Which here means
identical handling as for lists, but ultimately cast to tuple.

Tuples coerce to whatever the inner type(s) is/are.

## Bool

Because there's no real alternative option for bools, they are automatically
assumed to be flags. `long=True` is assumed, although both `long` and `short`
can be explicitly set, if you dont want the default name.

Additionally `bool` changes the "action" to "store_true", which results in the
argument accepting no additional "value" field.

## Literal

Literal unions, like `Literal["foo"] | Literal["bar"] | Literal["bar"]`,
translate into "choices" which ensure the value is one of the literal values.

This **could** be used to disambiguate a more complex type combination like
`tuple[Literal['int'], int] | tuple[Literal['float'], float]`, where it might
otherwise not have been possible to easily parse into the correct type.

## Enum

Enums are handled similarly to literals, except that you end up with the enum
variant instance as the returned type, rather than the literal input value.

## Dataclass (and alike)

The parsed value is `**splatted` into the annotated class. Note, this is only
really relevant for subcommands, because it's the only real way to get
\*\*splattable input values.
