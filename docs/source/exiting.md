# Exiting and Exit Codes

Cappa provides an [Exit](cappa.Exit) class to allow someone to gracefully exit
the program, without emitting a traceback.

```python
import cappa

def function():
    ...
    raise cappa.Exit(message="Oh no!", code=1)
    # or
    raise cappa.Exit("Oh no!", code=1)
    # or
    raise cappa.Exit(code=1)
    # or
    raise cappa.Exit("Graceful exit")  # i.e. status code 0!

@cappa.command(invoke=function)
...
```

## `Output` and Error Messages

By default, `cappa.parse` or `cappa.invoke` will internally construct an
[Output](cappa.Output) object which controls, among other things, how `Exit`
messages are handled. Both functions accept an `output` argument, allowing you
to control an `Output`'s settings.

Of note, there are two message templates:

- output_format (default `{message}`): Exit code == 0
- error_format (default `{short_help}\n\n[red]Error[/red]: {message}`): Exit
  code != 0

If, for example, you did not want to include `short_help` by default, and wanted
"Error" to be orange, you could do as follows:

```python
output = cappa.Output(error_format="[orange]Error[/orange]: {message}")
cappa.parse(Command, output=output)
```
