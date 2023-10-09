# Completion

```{note}
This feature is only supported when using the [cappa.backend](./backends.md).
```

Completion support is enabled by default. You can disable completion by sending
`completion=False` into your [parse](cappa.parse) or [invoke](cappa.invoke)
call.

By default, this adds a `--completion [generate/complete]` argument to the
resultant CLI. You can customize the name/visibility/help/etc of that argument
by supplying an [Arg](cappa.Arg) to the same argument (`completion=Arg(...)`).

## Enabling Completions

```{note}
Currently supported shells for completions include:

- Zsh
- Bash
- Fish

Submissions for additional shell support is very welcome.
```

`--completion generate` outputs `$SHELL`-specific source to power the
completions for the CLI A user of your CLI needs to redirect to the appropriate
default location for completions for that shell.

Alternatively they can write it to an arbitrary location and source the
resultant file in their shell-rc file, although this is not recommended!

```bash
mycli --completion generate > ~/.mycli.sh
```

## Completable Values

Currently cappa supports completions for

- `--option` long/short names
- Subcommand names
- Argument values

  By default this does local file completion for most argument types.

  If the argument defines logical "choices" (Enum, Union of Literals), those
  choices will be completed instead.

## Custom Completions

Any [Arg](cappa.Arg) can supply a `completion=function` argument to produce
arbitrary completions for that field. `function` (in this case) should be a
function which accepts a string (the partial string to complete), and returns a
list of [Completion](cappa.Completion)

```python
import cappa

def names(partial: str) -> cappa.Completion:
    names = ['Lucy', 'Bob', 'Ron']
    return [
        cappa.Completion(name, help='Available Names')
        for name in names
        if name.startswith(partial)
    ]

cappa.Arg(..., completion=names)
```
