# Rich

```bash
pip install 'cappa[color]'
```

This enables colored output of (primarily) the CLI's help text. The installation
of the dependency (currently rich-argparse) will automatically enable colored
output.

`invoke` or `parse` accept a `color: bool` argument which can be used to disable
the automatic enablement of the rich integration.

You can control individual styling of the help text by including rich directives
inside the help text text. For example `[bold]Help[/bold]`.

Per `rich` behavior, existence of the `NO_COLOR` environment variable will
disable colored output.
