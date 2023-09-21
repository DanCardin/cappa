# Manual Construction

The general intention of the library is that you use the inference system to
produce the most natural mapping between the source class definition and the
output CLI.

However, there's nothing preventing the manual construction of the command
definition, which allows one to completely decouple the CLI-specific annotations
from the class in question, if much more manually.

```python
from dataclasses import dataclass

import cappa
from cappa.annotation import parse_list


@dataclass
class Foo:
    bar: str
    baz: list[int]


command = cappa.Command(
    Foo,
    arguments=[
        cappa.Arg(name="bar", parse=str),
        cappa.Arg(name="baz", parse=parse_list(int), num_args=-1),
    ],
    help="Short help.",
    description="Long description.",
)


result = cappa.parse(command, argv=["one", "2", "3"])
# result == Foo(bar="one", baz=[2, 3])
```
