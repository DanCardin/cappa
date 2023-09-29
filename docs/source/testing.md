# Testing

You can **certainly** just directly call any invoke functions directly, manually
constructing and providing arguments yourself.

You can also just directly call [cappa.parse](cappa.parse) or
[cappa.invoke](cappa.invoke) yourself, with relatively little effort.

However, Cappa comes with a built in
[CommandRunner](cappa.testing.CommandRunner) which is meant to reduce the
verbosity of testing CLI commands and in overriding upstream [Dep](cappa.Dep).
With it, you can centralize any always-used options, such that only the options
which vary from test to test are provied inside the test bodies..

```{eval-rst}
.. autoapimodule:: cappa.testing
   :members: CommandRunner, RunnerArgs
   :noindex:
```

## Pytest

Cappa does not come with a built in pytest fixture because we assume that any
test suite which might benefit from a fixture will likely have other fixture
dependencies. Most users will want to customize the construction of their
`CommandRunner`, if they're going to use one at all.

It is very straightforward to define you own fixture to produce an appropriately
configured runner.

For example, let us describe a base CLI which depends upon an
[Explicit Dependency](./invoke.md#explicit-dependencies) on a configuration
dictionary which pulls data from the environment; which you need to override in
a fixture to work with the rest of your testing structure.

```{note}
See [Invoke dependency overrides](./invoke.md#overriding-dependencies) for additional
details.
```

Your existing code might look like this:

```python
import os
from typing import Annotated

import cappa

def config() -> dict:
    return {
        "env": os.getenv("ENV")
        "foo": os.getenv("FOO")
    }


def fn(config: Annotated[dict, cappa.Dep(config)]):
    print(config)

@cappa.command(invoke=fn)
class CLI:
    name: str
```

In your tests, you've decided you want to hard-code a specific alternative
`config` value. You could define a pytest fixture like so:

```python
import pytest
from cappa.testing import CommandRunner

from package import CLI, config

@pytest.fixture
def runner():  # Note `runner` could itself depend on other fixtures, in more complex scenarios
    return CommandRunner(CLI, deps={config: {"env": "test", "foo": "bar"}})

# OR
def stub_config() -> dict:
    return {
        "env": "test"
        "foo": "bar"
    }

@pytest.fixture
def runner():
    return CommandRunner(CLI, deps={config: cappa.Dep(stub_config)})
```

Then your tests will be able to omit most configuration, except for the item
under test:

```python
def test_foo(runner: CommandRunner):
    runner.invoke('name!')
```
