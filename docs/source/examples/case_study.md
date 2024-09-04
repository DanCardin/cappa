# Case Studies

These are examples a meant to show a bit more of a stream of consciousness tutorial
of sorts of how one might go from an empty python file to a CLI which does a
thing, and design decisions or evolutions that happen along the way.

## To-Do List

I am designing a CLI which manages a "To-Do List", a completely original idea
that I indend to sell one day. In order to interact said To-Do list, I'm going to
design a CLI interface with roughly the following command structure:

```bash
todo add 'Buy bananas'
todo remove 'Buy Bananas'
todo complete 'Buy Bananas'
```

First i'll start by getting a basic no-op executable running. Dataclasses are the
easiest way to define cappa-compatible classes (because they're built in), so I'll
go with that.

```python
from dataclasses import dataclass

import cappa

@dataclass
class Todo:
    ...


todo = cappa.parse(Todo)
print(todo)
```

```bash
$ python todo.py --help
Usage: todo [-h] [--completion COMPLETION]

  Help
    [-h, --help]               Show this message and exit.
    [--completion COMPLETION]  Use --completion generate to print
                               shell-specific completion source. Valid
                               options: generate, complete.

$ python todo.py
Todo()
```

Ok great, now let's add the "add" command

```python
from __future__ import annotations

from dataclasses import dataclass

import cappa

@dataclass
class Todo:
    command: cappa.Subcommands[AddCommand]


@dataclass
class AddCommand:
    todo: str

todo = cappa.parse(Todo)
print(todo)
```

Added `from __future__ import annotations` so that the classes could be defined
top-down sequentially, which I think makes understanding the flow of the commands
more intuitive.

Oh but oops:

```bash
$ python todo.py
Usage: todo {add-command} [-h] [--completion COMPLETION]

Error: A command is required: {add-command}
```

Ah yes, the name of my `AddCommand` class isn't the same as what I want the name of the literal CLI command to be. This should fix it:

```python
@cappa.command(name="add")
@dataclass
class AddCommand:
    todo: str
```

```bash
$ python todo.py add 'buy bananas'
Todo(command=AddCommand(todo='buy bananas'))
```

Now that the CLI has the shape I'd like it to have, time to implement the functionality.

I have a [few options](../invoke.md) for how to attach behavior to a given command/subcommand,
but in the interest of conciseness i'll simply my my dataclass callable.

```python
import json
from pathlib import Path

@cappa.command(name="add")
@dataclass
class AddCommand:
    todo: str

    def __call__(self):
        path = Path("todo.json")

        data = []
        if path.exists():
            data = json.loads(path.read_text())

        data.append(self.todo)
        path.write_text(json.dumps(data))
```

We'll also need to replace `cappa.parse` with `cappa.invoke`.

Let's also quickly add a `list` command to be able to actually test it out.

```python
...
@dataclass
class Todo:
    command: cappa.Subcommands[AddCommand | ListCommand]  # <- gotta remember to
                                                          # include the new command!
...

@cappa.command(name="list")
@dataclass
class ListCommand:
    def __call__(self):
        path = Path("todo.json")

        data = []
        if path.exists():
            data = json.loads(path.read_text())

        for item in data:
            print(f" - {item}")
```

Now we should be able to test it out:

```bash
$ python todo.py add 'buy bananas'
$ python todo.py add 'clean kitchen'
$ python todo.py list
 - buy bananas
 - clean kitchen
```

That's about it! You could keep going and add more commands; or implement it with something fancier
than a flat file.

Here is the final program.

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import cappa


@dataclass
class Todo:
    command: cappa.Subcommands[AddCommand | ListCommand]


@cappa.command(name="add")
@dataclass
class AddCommand:
    todo: str

    def __call__(self):
        path = Path("todo.json")

        data = []
        if path.exists():
            data = json.loads(path.read_text())

        data.append(self.todo)
        path.write_text(json.dumps(data))


@cappa.command(name="list")
@dataclass
class ListCommand:
    def __call__(self):
        path = Path("todo.json")

        data = []
        if path.exists():
            data = json.loads(path.read_text())

        for item in data:
            print(f" - {item}")


cappa.invoke(Todo)
```

## Slow Startup

```{admonition} ...Context...
Python CLIs can frequently have slow startup, the more imports and import-time
...stuff... that happens between the moment python starts up and the CLI parsing
logic executes.

This **can** be really annoying when all you're executing is `cli.py --help`, and
it's taking all of a second or more to run!

This is much _less_ of a problem for a library like `argparse`, whereas it can
**quickly** become a problem with something like `click`, where you're forced
to import the whole command tree preemptively in order to describe the CLI itself!
(Either that or remember to inline all your imports yourself!).

See [invoke](../invoke.md) docs for more detail!
```

I've got this really simply CLI program that's already taking an abnormally long
time to return on a simple `--help`! What gives!

```python
# cli.py
from __future__ import annotations

from dataclasses import dataclass

import cappa

from .mean import calculate_mean


@dataclass
class Slow:
    command: cappa.Subcommands[MeanCommand]


@cappa.command(name='mean', invoke=calculate_mean)
@dataclass
class MeanCommand:
    numbers: list[int]

cappa.invoke(Mean)


# mean.py
import pandas
from .slow import MeanCommand


def calculate_mean(command: MeanCommand):
    df = pandas.DataFrame(command.numbers)
    print(df.mean()[0])
```

```bash
time slow/cli.py --help
slow.py --help  0.82s user 0.07s system 165% cpu 0.541 total
```

840ms to do nothing! You know, I recall importing pandas is reasonably slow
maybe inline the import?

```python
# mean.py
def calculate_mean(command: MeanCommand):
    import pandas

    df = pandas.DataFrame(command.numbers)
    print(df.mean()[0])
```

```bash
time slow/cli.py --help
slow.py --help  0.20s user 0.07s system 165% cpu 0.541 total
```

Aha! That's a fair bit better. Although it's kind of annoying to have to remember
to inline slow imports throughout my program. Instead, lets have cappa defer the import
of the actual command for us!

```python
# cli.py
from __future__ import annotations

from dataclasses import dataclass

import cappa


@dataclass
class DeferImport:
    command: cappa.Subcommands[MeanCommand]


@cappa.command(name='mean', invoke='slow.mean.calculate_mean')
@dataclass
class MeanCommand:
    numbers: list[int]

cappa.invoke(DeferImport)


# mean.py
import pandas
from .slow import MeanCommand


def calculate_mean(command: MeanCommand):
    df = pandas.DataFrame(command.numbers)
    print(df.mean()[0])
```

Now, the CLI interface definition is nicely isolated from the actual implementation.
I dont need to import every possible code path in order to execute the CLI in the first
place, and we still have a nice fast CLI!

```bash
time slow/cli.py --help
slow.py --help  0.20s user 0.07s system 165% cpu 0.541 total
```
