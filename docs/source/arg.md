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
- Its help text is inferred from the class docstring's Argument section (either
  numpy or google style)

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
