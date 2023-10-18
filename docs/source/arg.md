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
corrresponding "action". The action is automatically inferred, most of the time,
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

Similarly to the [invoke][./invoke.md] system, you can use the type system to
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

## Environment Variable Fallback

```{eval-rst}
.. autoapimodule:: cappa
   :members: Env
   :noindex:
```
