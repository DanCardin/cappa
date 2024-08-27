# Invoke

If you're coming from `click` or `typer`, then `invoke` may likely be how you'll
want to describe your commands.

```{note}
See [Invoke Dependencies](./invoke.md#invoke-dependencies) for more information
about providing context/dependencies to your invoked functions.
```

You have a few options when choosing how to define the function that will be
invoked for your command.

1. you can simply make your dataclass callable:

   ```python
   @dataclass
   class Example:
       foo: int

       def __call__(self):
           print(self.foo)
   ```

   This has the benefit of simplicity, and avoids the need to decorate your
   class. The potential drawback, is that it couples the behavior to the class
   itself. However being forced to define function at the same location as your
   CLI definition may or may not be a drawback at all, for your usecase.

2. You can utilize the explcit `invoke=function` argument:

   ```python
   def function(example: Example):
       print(example.foo)

   @cappa.command(invoke=function)
   class Example:
       foo: int
   ```

   This **does** require you to decorate your class (which you may or may not
   have already needed to do). However, now `function` can be defined anywhere
   else in your codebase, decoupling the CLI definition from the implementation
   of the command itself.

3. You can use a module-reference string to target a callable:

   ```python
   # example.py
   @cappa.command(invoke='foo.bar.function')
   class Example:
       foo: int

   # foo/bar.py
   def function(example: Example):
       print(example.foo)
   ```

   The primary benefit of using string references, especially in large
   applications is import speed. This is equally true in other libraries, like
   click, where you need to essentially import your entire codebase in order to
   evaluate **just** the shape of the CLI enough to show help text.

   With string references, you **can** (whether or not you should) define your
   entire API shape in a standalone `cli.py` file with zero imports to the rest
   of your code. This should ensure your CLI has a fast time-to-helptext.

   Then at runtime, when the specific command/subcommand is chosen, only the
   relevant portions of your code need to be imported.

4. In simple cases, you can forgo classes entirely in favor of functions.

   ```python
   import cappa

   def cli(foo: int):
       return foo + 1

   result = cappa.invoke(cli)
   ```

   Such a CLI is exactly equivalent to a CLI defined as a dataclass with the
   function's arguments as the dataclass's fields, but with an unnameable class.

   There are various downsides to using functions. Naturally, you lose all
   ability to reference source classes as dependencies. Subcommands cannot be
   naturally defined as functions (since there is no type with which to
   reference the subcommand).

   As such, functions can only be used for certain kinds of CLI interfaces.
   However, they **can** reduce the ceremony required to define a given CLI
   command.

```{note}
When dealing with nested subcommands, only the "invoke" function for the **actually**
selected command/subcommand will be invoked.
```

Then, in order to opt into the invoke behavior, you need to call
[cappa.invoke](cappa.invoke), rather than [cappa.parse](cappa.parse).

```{eval-rst}
.. autoapifunction:: cappa.invoke
   :noindex:
```

## Implicit invoke imports

The `invoke` argument can be a direct reference to a function, as evidenced in
the single-file documentation examples.

However it can also be a string. When given as a string, it implies a fully
qualified module reference to a function. That is,
`src/package/module/submodule.py` with function `foo` in it, would be given be
the string `package.module.submodule.foo`.

```python
@cappa.command(invoke='package.module.submodule.foo')
class Example:
    ...
```

This can help to solve an issue that can be somewhat endemic to `click`
applications. Namely, that the act of describing the CLI shape forces the
programmer to transitively import all of the code that the CLI might ever
reference in any of its subcommands, regardless of whether they're actually
called in the actual command selected.

The usual approach, in click, is to inline imports into the click handler, thus
achieving the same thing. With cappa, it's much the same thing, except for the
inversion of control. The dynamic import is performed inside the `invoke` call,
which is mostly just a net reduction in boilerplate.

## Invoke Dependencies

`cappa.invoke` wouldn't be of much value if all it did was call argument-less
functions without any context. Thus, there is a system of "dependencies" that
cause arguments to your invoke functions to be supplied on demand, assuming the
CLI invocation is capable of fullfilling the dependencies.

There are two kinds of invoke dependencies, implicit and explicit.

### Implicit Dependencies

Implicit dependencies are known-unique object instances that the invoke system
can produce for your function without an explicit `Dep` annotation.

These objects include:

- Any command or subcommand user-defined objects upstream of the selected
  command/subcommand. For example:

  ```python
  @dataclass
  class SubExample:
      ...

  @dataclass
  class Example:
      subcommand: Annotated[SubExample, cappa.Subcommand]
  ```

  `Example` and `SubExample` will be available as implicit dependencies.

- A [cappa.Command](cappa.Command), which provides the `Command` object
  corresponding to the command/subcommand that was parsed.

- A [cappa.Output](cappa.Output), which can be used to produce (themed)
  stdout/stderr output.

```{note}
If there were another subcommand option, and the CLI invocation selected one or
the other of the two subcommand options, only the selected subcommand would have
been fullfilled.

It's therefore programmer error to describe an `invoke` function heirarchy which
depends on command options that would not have been constructed during parsing.
```

Given the implicit dependencies available to you, your `invoke` functions can
accept an argument of that type, and it will be automatically provided to the
function when invoked.

```python
def foo(command: Command, subcmd: Subcommand):
    ...

@cappa.command(invoke=foo)
...
```

### Explicit Dependencies

```{note}
If you're familiar with FastAPI's `Depends`, this will feel very similar.
```

Custom "explicit dependencies" can be built up, in order to have arbitrary
context injected into your invoked functions. Explicit dependencies must be
annotated with a `Dep` in order to be recognized as such.

```{note}
A function describing an explicit dependency can, itself, depend on other
explicit or implicit dependencies. This allows recursively building up a dependency
heirarchy.
```

```python
from typing_extensions import Annotated
from cappa import Dep

# No more dependencies, ends the dependency chain.
def config():
    return {
        'password': os.getenv('DB_PASS'),
    }


# Explicit dependency
def database(config: Annotated[Engine, Dep(config)]):
    return sqlalchemy.create_engine(...)


# Implicit dependency
def logger(example: Example):
    ...


# The actual invoke function, which can depend upon any/all of the above
def invoke_fn(
    example: Example,
    logger: Annotated[Logger, Dep(logger)],
    database: Annotated[Engine, Dep(database)]
):
    ...
```

- Any dependency can be referenced by any other dependency, or invoked function.
- Dependencies are evaluated only once per `cappa.invoke` call, regardless of
  how many dependencies transitively depend on it.
- Dependencies are evaluated on demand, in the order they're found, meaning they
  will not be evaluated if the specifically invoked function doesn't reference
  it.

#### Yield Dependencies

Generator functions can be used as implicit context managers. This can be useful
for certain kinds of dependencies which require some kind of
shutdown/post-action.

```python
from typing_extensions import Annotated
from cappa import Dep
import sqlalchemy

def connection():
    engine = sqlalchemy.create_engine(...)
    with engine.connect() as conn:
        yield conn

def invoke_fn(connection: Annotated[sqlalchemy.Connection, Dep(connection)]):
    ...
```

As with `contextlib.contextmanager`, the dependency's function should execute
exactly one yield given one execution through the function. The context of any
yield dependencies will remain "entered" up through the action of calling the
`invoke` function.

As such, it is probably **not** a good idea to return a context-managed resource
out of your invoke functions (`invoke_fn` above)! By the time you receive the
value (`foo = invoke(...)`) it will be exited.

#### Async Dependencies

Async functions can be supported as dependencies. See [asyncio](./asyncio.md)
documentation for details.

### Global Dependencies

The top-level [cappa.invoke](cappa.invoke) command accepts a `deps` argument
which denotes dependency functions which are called unconditionally.

These functions will be invoked before any explicit deps have been evaluated.
And given that they're executed unconditionally, it's impractical to define one
which depends on conditional dependencies like subcommands.

Thus it's generally only practical to use this to execute code which depends on
the top-level command's implicit dependency. Although it can certainly have
**no** dependencies, you could also just call that function before calling
`invoke` in the first place.

```python
@dataclass
class Command:
    a: int


def dep(command: Command):
    ...


def main():
    cappa.invoke(Command, deps=[dep])
```

Note, given as a Sequence (i.e. list, tuple), you can just provide the source
function which should act as a `Dep`, and it will be automatically coerced into
a proper `Dep`.

### Overriding Dependencies

```{note}
See [Testing](./testing.md) for additional details. This option is primarily
motivated to aid stubbing dependencies for testing.
```

An alternative to the above sequence input for `deps`, you can instead supply a
Mapping, where the key is the "source" dependency function (i.e. the function a
dependent invoke function would reference) and the value is the actual
dependency which should be used in its place.

For example,

```python
# We've decided we want to override "foo"
def foo():
    ...

# and here is a function which depends upon it.
def invokable_function(foo: Annotated[int, Dep(foo)]):
    ...
```

You can either override the dep with another, "stub" dep by explicitly wrapping
the value with a `Dep`

```python
def stub_dep():
    return 4

cappa.invoke(Command, deps={foo: Dep(stub_dep)})
```

Or you can directly provide a literal stub value for the dep, by providing the
value without a wrapping `Dep`.

```python
cappa.invoke(Command, deps={foo: 4})
```

### Unfulfilled Dependencies

Should an argument be neither an explicitly annotated `Dep`, nor typed as one of
the available implicit dependencies in the heirarchy, then it's considered
unfulfilled.

If the argument to the callable has a default value, then the argument will
simply be omitted, and the function called anyway.

In the event the argument is required, a `RuntimeError` will be raised and CLI
processing will stop.
