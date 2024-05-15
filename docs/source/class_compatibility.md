# Dataclasses/Pydantic/Attrs

All of the documentation uses `dataclasses` specifically, because it is built
into the standard library since python 3.7.

With that said, any dataclass-like class description pattern should be able to
be supported with relatively little effort. Today Cappa ships with adapters for:

- [dataclasses](https://docs.python.org/3/library/dataclasses.html),
- [Pydantic](https://pydantic-docs.helpmanual.io/) (v1/v2)
- [attrs](https://www.attrs.org)
- [msgspec](https://jcristharif.com/msgspec/)

Additionally the `default` and/or `default_factory` options defined by each of
the above libraries is used to infer CLI defaults.

## PEP681

You can opt to `@cappa.command(...)` with or without the double-decorator.

```python
@cappa.command(...)
@dataclass
```

`@cappa.command(...)` works without the `@dataclass` decorator at runtime,
because it detects whether the class is one of the supported types (dataclasses,
pydantic, attrs), and adds `@dataclass` to the declared class automatically, if
one is not detected.

So long as you use a a [PEP681 compliant](https://peps.python.org/pep-0681/)
type checker (e.g. pyright, Mypy>=1.2).

## Metadata

Finally, `dataclasses` and `attrs` both allow a `metadata`. You can optionally
utilize that metadata field to supply `Arg` and `Subcommand` instances, as an
alternative to using `Annotated`.

The following snippets of code are equivalent:

```python
arg: Annotated[str, cappa.Arg(short=True, help='help!')]

# vs

arg: str = dataclasses.field(metadata={'cappa': cappa.Arg(short=True, help='help!')})
# same with attrs
```
