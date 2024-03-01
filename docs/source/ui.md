# UI

Cappa includes an optional TUI (terminal user interface) that renders your CLI
as an interactive form. It is built on [Textual](https://textual.textualize.io/)
and can be served in a browser via
[textual-serve](https://github.com/Textualize/textual-serve).

## Installation

```bash
# TUI only
pip install cappa[ui]

# TUI + browser serving
pip install cappa[web]
```

## Usage

Given a standard cappa-annotated class:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Union
from typing_extensions import Annotated

import cappa
from cappa.ui import run, serve, make_app


@dataclass
class Deploy:
    """Deploy a service to an environment."""

    service: str
    env: Annotated[
        Literal["dev", "staging", "prod"],
        cappa.Arg(long="--env"),
    ] = "dev"
    dry_run: bool = False


@cappa.command(name="myapp")
@dataclass
class MyApp:
    sub: Annotated[Union[Deploy, ...], cappa.Subcommand()]
```

### TUI (terminal)

```python
if __name__ == "__main__":
    run(MyApp)
```

Or from the command line:

```bash
python -m cappa.ui.tui mymodule:MyApp
```

### Web (browser)

Serves the TUI over WebSocket so any browser can connect. Requires `cappa[web]`.

```python
if __name__ == "__main__":
    serve(MyApp)
```

Or from the command line:

```bash
python -m cappa.ui.web mymodule:MyApp
```

### Development (live reload)

For file-watch reload during development, expose a module-level `App` instance
and use `textual serve`:

```python
# mymodule.py
from cappa.ui import make_app

app = make_app(MyApp)
```

```bash
textual serve mymodule:app --dev
```

## Features

- **Command tree** — sidebar listing all subcommands; clicking switches the form.
- **Form** — one control per argument: text input, checkbox (bool), or select
  (choices / `Literal`).
- **Search** — filter visible arguments by name or help text.
- **Preview** — live CLI string showing exactly what will be executed.
- **Close & Run** (`ctrl+r`) — invokes the CLI with the current form values.
- **Command info** (`ctrl+o`) — modal showing argument counts and subcommands.
- **About** (`?`) — modal showing the command description.

## Keyboard shortcuts

| Key | Action |
|---|---|
| `ctrl+r` | Exit & run with current values |
| `ctrl+t` | Focus command tree |
| `ctrl+o` | Open command info |
| `?` | Open about dialog |
| `escape` | Close modal |
