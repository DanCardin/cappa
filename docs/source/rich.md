# Rich

## Color

Colored output, including help-text generation, is automatically enabled.
[invoke](cappa.invoke) or [parse](cappa.parse) both accept a
`color: bool = True` argument which can be used to enable/disable the colored
output directly. Alternatively, rich automatically respects the `NO_COLOR`
environment variable for disabling colored output.

You can control individual styling of the help text by including rich directives
inside the help text text. For example `Arg(help="I need [bold]Help[/bold]!")`.

### Theming

You can define your own rich `Theme` object and supply it into
[invoke](cappa.invoke) or [parse](cappa.parse), which will used when rendering
help-text output (and error messaging).

Cappa's theme defines and uses the follwing style groups, which you would need
to also supply:

- `cappa.prog`
- `cappa.group`
- `cappa.arg`
- `cappa.arg.name`
- `cappa.subcommand`
- `cappa.help`

## Prompt/Confirm

Cappa does not come with a native prompt/confirm option. However it does ship
with built-in integration with `rich.prompt.Prompt`.

You can directly make use of confirm/prompt from within your code anywhere, and
it should "just work"

```python
from rich.prompt import Prompt

name = Prompt.ask("Enter your name")
```

Alternatively, a `Prompt` object can be used as a `default=` value for a
[cappa.Arg](cappa.Arg) instance.

```python
import cappa
from rich.prompt import Prompt

@dataclass
class Test:
    name: Annotated[str, cappa.Arg(default=Prompt("Enter one of these", choices=['one', 'two', 'three']))]

result = parse(Test)
```

In the event the value for that argument was omitted at the command-line, the
prompt will be evaluated.

```{note}
Input prompts can be a hazzard for testing. `cappa.rich.TestPrompt` can be used
in any CLI-level testing, which relocates rich's `default` and `stream` arguments
off the `.ask` function.

You can create a `TestPrompt("message", input='text input', default='some default')`
to simulate a user inputting values to stdin inside tests.
```

## Pretty Tracebacks

Prettily backending tracebacks can be a UX improvement for your CLI. Cappa does
not define any specific integration with rich for tracebacks, given that you
simply install rich's native traceback handler before calling parse/invoke.

```python
import cappa
from rich.traceback import install

def main():
    install(show_locals=True)
    cappa.invoke(...)
```
