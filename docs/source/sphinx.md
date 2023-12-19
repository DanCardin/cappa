# Sphinx/Docutils Directive

As of version 0.16.0, Cappa ships with a "docutils" directive capable of
rendering the CLI to docutils/sphinx documentation.

In sphinx, you would load this in `conf.py`, by adding `"cappa.ext.docutils"` to
the list of extensions:

```python
extensions = [
    ...
    "cappa.ext.docutils",
]
```

The module path to the CLI object is the only required argument. All other
options are...optional.

The default configuration is equivalent to:

```rst
.. cappa:: <required.module.path.to.Object>
   :style: terminal
   :terminal-width: 0
```

or with MyST:

````md
```{cappa} <required.module.path.to.Object>
:style: terminal
:terminal-width: 0
```
````

Options/customization currently include:

- style: "native" or "terminal" (defaults to "terminal"). "terminal" renders the
  `--help` text as it would have rendered at the terminal. "native" renders the
  CLI structure as native docutils sections/text. Set like `:style: terminal`.

- terminal-width: The fixed-width at which to render the terminal-style help
  text. Defaults to 70. Set like `:terminal-width: 80`. Note, you can also set
  the width to 0, to utilize browser line-wrapping, although it will not look
  identical to the line-wrapping in the terminal.

Customization is likely increase over time purely based off user requests!
