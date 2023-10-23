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

## Cappa backend

This is the default backend.

The main "headline" feature you get when using the cappa backend is: Automatic
[completion](./completion.md) support. However, generally it's going to be
easier to support arbitrary features with the native parser than with an
external backend.

It is roughly 1/3 the size in LOC, given that much of the featureset and
flexibility of argparse are unused and a source of contention with cappa's
design (The whole native parser is ~500 LOC, whereas just the argparse adapter
is ~350 LOC).

## Argparse backend

Cappa was originally written against the argparse backend, a testament to the
flexibility of its API, that it's even possible.

The main "problem" with the argparse backend is that cappa replaces much of the
higher level features it provides at a higher level, outside the parser itself.
A majority of the backend's source is working around specific argparse API
decisions, and redefining argparse's objects with necessary modifications.

This backend will be maintained for the foreseeable future, if for no other
reason than it's a useful benchmark for parser compatibility.

Some potential reasons you want want to use the argparse backend:

- Argparse is also obviously fairly battle tested, and therefore theoretically
  less likely to contain bugs that might exist in the native cappa backend.
- Argparse may have pre-existing libraries designed to extend it. (While we cant
  guarantee an arbitrary argparse extension will function correctly with cappa,
  but to the extent possible, it's a goal that they should be supported if
  possible.
