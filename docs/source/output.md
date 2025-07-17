# Console Output

By default, `cappa.parse` or `cappa.invoke` will internally construct an
[Output](cappa.Output) object which controls the format of all console
output, including how [Exit](cappa.Exit) and errors are formatted.

Alternatively [cappa.parse](cappa.parse) and [cappa.invoke](cappa.invoke) both accept
`Output` instances as an optional input, allowing you to customize the instance or
otherwise make use of it before/after the CLI parse time.

Any `Output` output will automatically make use of [rich](rich), and thus has access to
its native styling syntax, and the ability to output native rich constructs.

## Producing Output
An [invoke](cappa.invoke) handler which depends on an argument annotated as `Output`
will be automatically provided with the `Output` instance.

```python
import cappa
from dataclasses import dataclass

@cappa.command()
def cli(output: Output):
    output("Hi!") # e.g. output.output("Hi!")


cappa.invoke(cli)

# or

@cappa.command(invoke=cli)
@dataclass
class CLI:
    ...

cappa.invoke(cli)
```

```{note}
If you're familiar with `click`, `click.echo` is roughly equivalent to `Output.output`.
```

You can alternatively call `Output.error` to make use of error-specific default formatting/coloring

## Exiting and Exit Codes

Cappa provides an [Exit](cappa.Exit) class to allow someone to gracefully exit
the program, without emitting a traceback.

```python
raise cappa.Exit(message="Oh no!", code=1)
# or
raise cappa.Exit("Oh no!", code=1)
# or
raise cappa.Exit(code=1)
# or
raise cappa.Exit("Graceful exit")  # i.e. status code 0!
```

If [Exit](cappa.Exit) is encountered anywhere within cappa's running context (e.g. an invoke handler,
a parser, an action, etc), it will automatically `Output` the message using the method appropriate
to the exit code (`code=0` -> `Output.output` and `code>0` -> `Output.error`), before gracefully exiting.

## Customizing default formatting
[cappa.parse](cappa.parse) and [cappa.invoke](cappa.invoke) both accept `Output`
instances as an optional input, allowing you to customize default formatting.

- output_format (default `{message}`): Exit code == 0
- error_format (default `{short_help}\n\n[red]Error[/red]: {message}`): Exit
  code != 0

If, for example, you did not want to include `short_help` by default, and wanted
"Error" to be orange, you could do as follows:

```python
output = cappa.Output(error_format="[orange]Error[/orange]: {message}")
cappa.parse(Command, output=output)
```

## API

```{eval-rst}
.. autoapimodule:: cappa
   :members: Output
   :noindex:
```
