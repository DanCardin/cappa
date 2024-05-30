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
.. autoapimodule:: cappa
   :members: Arg
   :noindex:
```

## Action

Obliquely referenced through other `Arg` options like `count`, every `Arg` has a
corresponding "action". The action is automatically inferred, most of the time,
based on other options (i.e. `count`), the annotated type (i.e. `bool` ->
`ArgAction.set_true/ArgAction.set_false`, `list` -> `ArgAction.append`), etc.

However the inferred action can always be directly set, in order to override the
default inferred behavior.

### Custom Actions

```{note}
This feature is currently experimental, in particular because the parser state
available to either backend's callable is radically different. However, for an
action callable which accepts no arguments, behaviors is unlikely to change.
```

In addition to one of the literal `ArgAction` variants, the provided action can
be given as an arbitrary callable.

The callable will be called as the parser "action" in response to parsing that
argument.

```{note}
Custom actions may interfere with general inference features, depending on what you're
doing (given that you're taking over the parser's duty of determining how the
code ought to handle the argument).

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
likely be exposed through this interface in the future.

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
.. autoapimodule:: cappa
   :members: Argction
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

## Num Args

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

## Default

Controls the default argument value at the CLI level. Generally, you can avoid
direct use of cappa's default by simply using the source class' native default
mechanism. (i.e. `foo: int = 0` or `foo: int = field(default=0)` for
dataclasses).

However it can be convenient to use cappa's default because it does not affect
the optionality of the field in question in the resultant class constructor.

### Environment Variable Fallback

You can also use the default field to supply supported kinds of
default-value-getting behaviors.

`Env` is one such example, where with
`Arg(..., default=Env("FOO", default='default value'))`, cappa will attempt to
look up the environment variable `FOO` for the default value, if there was no
supplied value at the CLI level.

```{eval-rst}
.. autoapimodule:: cappa
   :members: Env
   :noindex:
```

## Groups (and Mutual Exclusion)

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

- `Group`: Instances of `Group` are the normalized form of the above two shorthand
  options (which are ultimately coerced into `Group`s).

  `Group` additionally has an `exclusive: bool` option, which can be used to indicate
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
