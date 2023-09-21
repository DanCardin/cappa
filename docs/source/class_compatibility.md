# Dataclasses/Pydantic/Attrs

All of the documentation uses `dataclasses` specifically, because it is built
into the standard library since python 3.7.

With that said, any dataclass-like class description pattern should be able to
be supported with relatively little effort. Today Cappa ships with adapters for
[dataclasses](https://docs.python.org/3/library/dataclasses.html),
[Pydantic](https://pydantic-docs.helpmanual.io/), and
[attrs](https://www.attrs.org).

Additionally the `default` and/or `default_factory` options defined by each of
the above libraries is used to infer CLI defaults.

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
