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
