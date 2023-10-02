# Parser Backends

Cappa is designed in two parts:

- The "frontend", which is the vast majority of the public API. All the
  available objects and functions, the annotation inference engine, the
  invoke/dependency system, etc.

- The parser "backend", which takes the object graph produced by your CLI
  definition and parses the raw CLI (into a form the "frontend" can understand).

  The backend also controls the help-text formatter

There are currently two backend options:

- A custom parser maintained inside cappa itself
- An Argparse backend

A large majority of tests are run with both parsers to ensure general
compatibility. Any difference in backend parse **behavior** should be considered
a bug. However, error **messaging** will not match exactly across backends.

You select a backend by providing the `backend` argument to [parse](cappa.parse)
or [invoke](cappa.invoke).

```python
import cappa

cappa.parse(..., backend=cappa.argparse.backend)
cappa.invoke(..., backend=cappa.argparse.backend)

cappa.parse(..., backend=cappa.backend)
cappa.invoke(..., backend=cappa.backend)
```

## Argparse backend

Currently this is the default backend.

Argparse is obviously fairly battle tested, and has some existing corpus of
libraries designed to extend it. While we cant guarantee an arbitrary argparse
extension will function correctly with cappa, but to the extent possible, that
is a goal.

This backend will be maintained for the foreseeable future.

The main problem with the argparse backend is that cappa replaces much of the
higher level features it provides at a higher level, outside the parser itself.

A majority of the backend's source is working around specific argparse API
decisions (a testament to the flexibility of its API, that it's even possible),
and redefining argparse's objects with slight, necessary modifications.

## Cappa backend

Some "headline" features you get when using the cappa backend:

- Automatic [completion](./completion.md) support
- Automatic rich-powered, colored help-text formatting

But generally, it's going to be easier to support arbitrary features with a
custom parser than with an external backend.

This backend is not currently the default due to its relative infancy. It will,
however, **become** the default before 1.0 of the library.
