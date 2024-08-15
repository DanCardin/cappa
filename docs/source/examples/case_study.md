# Examples

## Case Study

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
