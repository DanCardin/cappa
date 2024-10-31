# Why

A fair question. The incumbents, with click/typer and argparse have been readily
serving python for a long time, and will certainly continue to do so.

Having use the "derive API" from Rust's
[Clap](https://docs.rs/clap/latest/clap/_derive/index.html) library, it's just
really really nice to use, because the API is so natural. It became obvious that
python could obviously support a similar API and it was surprising that one
didn't already exist.

Hopefully with `cappa`, you get the flexibility to utilized either the
command-forward design given by `click`/`typer` or the manual handling given by
`argparse` (and even `clap`).

## Why not click?

I've used click for years, it's certainly a good library. There are some aspects
of its design that make it really frustrating to use beyond small projects with
a single entrypoint.

- Many of the issues stem from the fact that click wraps the called function,
  and changes its behavior. Calling the resultant function invokes the CLI.

  You want to call that function in two places? you need to use `click.invoke`.

  You want to do this in tests? You need to deal with its `ClickRunner` that
  accepts args as a list of string, and output in terms of stdout and stderr. In
  terms of tests, this is really large drop in UX relative to a plain function
  (with args) you can call.

  You want to avoid click-isms in either case? You need to (basically) duplicate
  your function. One wrapped in click decorators, which just defers to a similar
  function that just accepts the arguments.

  - `Cappa` inverts the relationship to invoked functions. You do not wrap the
    functions, so they end up just being plain functions you can call in any
    scenario.

    And in the case of the decorated classes, the resultant class is directly
    returned. It should act exactly like the dataclass/pydantic model you
    defined.

    Even parsing or invoking the CLI through `Cappa`'s mechanisms to parse the
    argv, in tests for example, the result is **much** more similar to just
    executing the function in the first place.

- Click imperitively accumulates the CLI's shape based on where/how you combine
  groups and commands. Intuiting what resultant CLI looks like from the series
  of click commands strung together is not obvious.

  - `Cappa` centrally declares the CLI shape based on types. For all of the
    reasons pydantic models can be easily used to describe a potentially deeply
    nested schema, with `Cappa` it's very easy to look at the model and
    determine the total set of arguments and subcommands relative to it.

- Because click tightly couples the called function with click itself, a large
  enough CLI will inevitably slow down starup because you're forced to
  transitively import your whole codebase in order to describe the state of the
  CLI itself.

  - `Cappa` allows you to define the CLI in a way where you **could** define the
    CLI shape/calls in complete isolation with no (lazy) imports to the rest of
    your code.

- The Click "Context" appears to be its only mechanism for providing
  non-argument dependencies to commands/subcommands. And `pass_context` (and the
  mutation of the context) is a very blunt tool, that secretly couples the
  implementations of different commands together.

  - `Cappa` uses the same dependency resolution mechanisms it uses for arguments
    to provide the result of arbitrary functions to your commands (Reminiscent
    of FastAPI's `Depends`).

    For example, some subcommand require loading config, some commands require a
    database connection (or whatever) which itself depends on that config. What
    would be a, relatively, more difficult task using the click context (or
    manually littering the loading of these things inside the bodies of the
    commands) uses the same API as the rest of `Cappa`.

- With `click`, it's impossible(? or at least not clear how) to perform
  `argparse`-like (or Clap) ability to just parse the structure and return the
  parsed output shape.

  - `Cappa` provides a separate `parse` function and `invoke` function. You can
    choose either style, or both.

## Why not [Typer](https://typer.tiangolo.com/)

Typer has a lot of good ideas, inspired by Hug before it. While the actual
inspiration for Cappa is
[Clap](https://docs.rs/clap/latest/clap/_derive/index.html), the annotation
results for arguments end up looking a lot like typer's args!

Unfortunately, Typer is **basically** Click (with type-inferred arguments), and
has all of the same drawbacks.

If `tiangolo` hadn't based typer on click, it's not crazy to imagine that
`cappa` look something like what he might have come up with. In particular the
`Dep` feature of `cappa` looks and feels a lot like the `Depends` feature of
FastAPI.

Further, cappa provides more comprehensive type inference (e.g. translating complex
types like `foo: tuple[int, str] | None` into their logical CLI argument shapes.
As the input shapes become more complex, typer's inference begins to lose out (at
time of writing).

## Why not argparse?

The imperative style of argparse can just be tedious to read/write, and hard to
intuit what the shape of the resultant CLI will look like. `Cappa` currently
uses argparse as the underlying argument parsing library, because it is the most
straightforward, maintained, python library for building this sort of
declarative system upon.

With argparse you lose the useful aspect of click's functional composability.
Argparse's API is relatively complex (especially when dealing with subcommands),
and performing the dispatch of subcommands to functions with scoped arguments is
extremely complicated.

The sweet spot for Argparse's API is single-level commands with a bunch of
options. Beyond that, it becomes difficult to understand.

## Others/New Contenders

I was recently made aware of a couple of other options that seem similarly
inspired, namely:

### [Tyro](https://brentyi.github.io/tyro/)

At a glance, this seems most similar to Cappa of any alternatives. If we take a
look at
[their own comparisons](https://brentyi.github.io/tyro/goals_and_alternatives/),
Cappa seems to check all of the boxes Tyro does.

It certainly **feels** different when authoring an identical CLI with one or the
other, but they **do** seem to mostly overlap in terms of functionality. Cappa's
`invoke`/dependency system is probably the most standout difference maker, if
the overall differences in their API are not important to you.

It **seems** to be somewhat tailored towards
[datascience(?) usecases by translating object shapes into cli arguments.](https://brentyi.github.io/tyro/examples/02_nesting/01_nesting/)
By contrast Cappa is tries to be able to describe a specific/arbitrary CLI shape
**using** objects, essentially inverting the focal point.

Tyro is built on top of argparse (and we have an argparse backend, wins for
argparse!), although Cappa's backend was specifically built because the argparse
backend is fairly limiting in terms of ability to hook into the parser for
things like completions, and error reporting.

### [Clipstick](https://github.com/sander76/clipstick)

Explicitly avoids use of Annotated, which ultimately limits its flexibly. Without
additional configuration data, there's only so much it can support.

Otherwise it seems very similarly inspired and thus looks rather nice.

### Pydantic-based options

I hope it should be uncontroversial to say that either option are a clear subset of
at least the CLI shapes you can produce with click/argparse. And cappa is meant to
reside in that category.

These options probably do their job (of producing a pydantic model given CLI arguments)
consisely and well! But they dont **seem** to be targeted at producing CLIs of
arbitrary shape like click/argparse/typer.

And you can use pydantic models with cappa, so I think you can arrive at many of
the same benefits as you might find in either option, namely flexible input value
parsing and loading defaults from environment variables, but you can do so for any
CLI shape you might want to produce.

#### [Pydantic-CLI](https://github.com/mpkocher/pydantic-cli)

Doesn't support positional arguments, only supports inferring "simple" types. While
it does support subcommands, it seems to do so in a way that's single-level only?

Again, it seems much more oriented at translating CLI arguments into an
instance of a pydantic model, **rather than** describing an arbitrary CLI
shape while utilizing types/models.

#### [Pydantic-Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#the-basics)

Again, you can tell that (I think) from the way nested models are translated into a
flattened list of options, that it's very focused on instantiating a pydantic model
from a given set of CLI arguments, rather than describing an arbitrarily shaped CLI.

It does appear to support subcommands and positional arguments, but it's (imo) done
sort of weirdly, which seems to be the result of bolting the CLI parsing onto pydantic rather
than the other way around. 

There appear to be a lot of maybe convenient automatic parsing features that translate
arguments from various json or other input formats into the model fields. If you **dont**
want all these different input modes, it's not immediately obvious how to turn them all
off and arrive at more "normal" CLI input parsing.

Cappa provides more comprehensive type inference (e.g. translating complex types like
`foo: tuple[int, str] | None` into their logical CLI argument shapes. Pydantic-settings
seems to prefer accepting arbitrary inputs as JSON automatically and using pydantic's
native parsing capabilities to attempt to interpret the values, rather than translating
them into "traditional" CLI behaviors.
