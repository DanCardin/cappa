# Examples

Below is a collection of standalone examples of specific argument/CLI behavior
one might want, with comparison examples of how it might be done in each of
Click/Typer/Argparse, where relevant.

Please bring up any specific usage questions about comparisons between Cappa
and other libraries as an [issue](https://github.com/dancardin/cappa/issues) or
a [discussion](https://github.com/dancardin/cappa/discussion). The list below can
 and should grow in response to feature-comparisons which are not clear just from
 reading the cappa-specific documentation.

## Custom Option Value Name

i.e. "FOO" in

```
$ prog --help
Usage: prog --some-arg FOO
```

````{admonition} Cappa
:class: dropdown

```python
from typing import Annotated
from dataclasses import dataclass
import cappa

@dataclass
class Args:
    some_arg: Annotated[str, cappa.Arg(value_name='FOO')]

cappa.parse(Args)
```
````

````{admonition} Argparse
:class: dropdown

```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--some-arg", metavar="FOO")
parser.parse_args()
```
````

````{admonition} Click
:class: dropdown

```python
import click

@click.command()
@click.option('--some-arg', metavar="FOO")
def main():
   ...

main()
````

````{admonition} Typer
:class: dropdown

```python
from typing_extensions import Annotated
import typer

def main(some_arg: Annotated[str, typer.Argument(metavar="FOO")]):
   ...

typer.run(main)
```
````

## Unbounded option arguments

i.e. `prog --foo 1 2 3 4 ...`

````{admonition} Cappa
:class: dropdown

```python
from typing import Annotated
from dataclasses import dataclass
import cappa

@dataclass
class Args:
    foo: Annotated[list[str], cappa.Arg(num_args=-1)


print(cappa.parse(Args))
```
````

````{admonition} Argparse
:class: dropdown

```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--foo", nargs="*")
print(parser.parse_args())
```
````

```{admonition} Click/Typer
:class: dropdown

Click's (and thus Typer) parser, at time of writing, appears to not support this
feature
```

## Interactive Prompt

```
$ prog
What's your name?: Ron
```

````{admonition} Cappa
:class: dropdown

```python
from typing import Annotated
from dataclasses import dataclass
from rich.prompt import Prompt
import cappa

@dataclass
class Args:
    some_arg: Annotated[str, cappa.Arg(default=rich.Prompt("What's your name?"))]

cappa.parse(Args)
```
````

```{admonition} Argparse
:class: dropdown

Argparse requires custom code or a [third party library](https://pypi.org/project/argparse-prompt/)
to support this feature
```

````{admonition} Click
:class: dropdown

```python
import click

@click.command()
@click.option('--name', prompt="What's your name?")
def main(name):
    ...

main()
````

````{admonition} Typer
:class: dropdown

```python
import typer
from typing_extensions import Annotated

def main(name: str, lastname: Annotated[str, typer.Option(prompt="What's your name?")]):
    ...

typer.run(main)
```
````

## Subcommands

```
$ prog double 123
246
$ prog print --title bar
Bar
```

````{admonition} Cappa
:class: dropdown

```python
from __future__ import annotations
from dataclasses import dataclass
import cappa


@dataclass
class Args:
    command: cappa.Subcommands[Double | Print]


@dataclass
class Double:
    arg: int

    def __call__(self):
        print(self.arg * 2)


@dataclass
class Print:
    text: str
    title: bool = False

    def __call__(self):
        text = self.text.title() if self.title else self.text
        print(text)


cappa.invoke(Args)
```

Not the shortest, but (I think) it's still very intelligble. Certainly, the extra
line or two dedicated to turning each command into a type can add some extra heft.

The mechanism by which the subcommands are declared is (I think) the clearest of the 4.
````

````{admonition} Argparse
:class: dropdown

```python
import argparse


def double(arg: int):
    print(arg * 2)


def print_command(text: str, title: bool):
    text = text.title() if title else text
    print(text)


parser = argparse.ArgumentParser()
subcommand = parser.add_subparsers(dest="command")

double_subcommand = subcommand.add_parser(name="double")
double_subcommand.add_argument("arg", type=int)

print_subcommand = subcommand.add_parser(name="print")
print_subcommand.add_argument("text")
print_subcommand.add_argument("--title", action="store_true", default=False)

args = parser.parse_args()
if args.command == "double":
    double(args.arg)
elif args.command == "print":
    print_command(args.text, args.title)
```

I had to look at the docs to implement, because the `parser.add_subparsers`
-> `subparser.add_parser()` API is non-intuitive.

Obviously the programmer needs to implement the subcommand dispatch that's handled
for you in all the other options.

Finally the resultant `args` namespace is completely untyped and you need to hope
that the shape you described matches how you access it.
````

````{admonition} Click
:class: dropdown

```python
import click


@click.group()
def main():
    ...


@main.command()
@click.argument("arg", type=int)
def double(arg: int):
    print(arg * 2)


@main.command(name="print")
@click.argument("text")
@click.option("--title", is_flag=True, default=False)
def print_command(text: str, title: str):
    text = text.title() if title else text
    print(text)


main()
```

Subcommands (particularly nested ones beyond the complexity of this example) are
click's strong suit.

The main annoyance is that it's fairly repetitive. You need to manually choose the correct
mapper/type, match the argument names yourself, and repeat the types if you want a typed
function.
````

````{admonition} Typer
:class: dropdown

```python
import typer

app = typer.Typer(name="example")


@app.command()
def double(arg: int):
    print(arg * 2)


@app.command("print")
def print_command(text: str, title: bool = False):
    text = text.title() if title else text
    print(text)


app()
```

Typer is certainly the shortest in this example, and has the least repetition.
This is probably Typer's clearest case. It very simply and directly solves
the repetition/mapping problem of click.
````
