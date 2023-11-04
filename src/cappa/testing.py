from __future__ import annotations

import typing
from dataclasses import dataclass, field

from typing_extensions import Unpack

import cappa

__all__ = [
    "CommandRunner",
    "RunnerArgs",
]


class RunnerArgs(typing.TypedDict, total=False):
    """Available kwargs for `parse` and `invoke` function, to match `CommandRunner` fields."""

    obj: type
    deps: typing.Sequence[typing.Callable]
    backend: typing.Callable | None
    output: cappa.Output | None
    color: bool
    version: str | cappa.Arg
    help: bool | cappa.Arg
    completion: bool | cappa.Arg


@dataclass
class CommandRunner:
    """Object to hold common parse/invoke invocation state, for testing.

    Accepts almost identical inputs to that of `parse`/`invoke`. The notable
    deviation is `argv`.

    Whereas the original functions accept argv as a single-argument list;
    `CommandRunner` accepts `base_args` at the class-constructor level, which
    is concatenated with the `CommandRunner.parse` or `CommandRunner.invoke`
    `*args`, to arrive a the total set of input args.

    Example:
        Some base CLI object

        >>> from dataclasses import dataclass
        >>>
        >>> import cappa
        >>>
        >>> @dataclass
        ... class Obj:
        ...     first: str
        ...     second: str = '2'

        Create an instance with no arguments means there is no default state

        >>> runner = CommandRunner()
        >>> runner.parse('one', obj=Obj)
        Obj(first='one', second='2')

        Or create a runner that always uses the same base CLI object, and default base command

        >>> runner = CommandRunner(Obj, base_args=['first'])

        Now each test, can customize the behavior to suit the test in question.

        >>> runner.parse(color=False)
        Obj(first='first', second='2')

        >>> runner.parse('two')
        Obj(first='first', second='two')
    """

    obj: type | None = None
    deps: typing.Sequence[typing.Callable] | None = None
    backend: typing.Callable | None = None
    output: cappa.Output | None = None
    color: bool = True
    version: str | cappa.Arg | None = None
    help: bool | cappa.Arg = True
    completion: bool | cappa.Arg = True

    base_args: list[str] = field(default_factory=lambda: [])

    def coalesce_args(self, *args: str, **kwargs: Unpack[RunnerArgs]) -> dict:
        return {
            "argv": self.base_args + list(args),
            "obj": kwargs.get("obj") or self.obj,
            "backend": kwargs.get("backend") or self.backend,
            "output": kwargs.get("output") or self.output,
            "color": kwargs.get("color") or self.color,
            "version": kwargs.get("version") or self.version,
            "help": kwargs["help"] if "help" in kwargs else self.help,
            "completion": kwargs["completion"]
            if "completion" in kwargs
            else self.completion,
        }

    def parse(self, *args: str, **kwargs: Unpack[RunnerArgs]):
        final_kwargs = self.coalesce_args(*args, **kwargs)
        return cappa.parse(**final_kwargs)

    def invoke(self, *args: str, **kwargs: Unpack[RunnerArgs]):
        final_kwargs = self.coalesce_args(*args, **kwargs)
        deps = kwargs.get("deps") or self.deps
        return cappa.invoke(**final_kwargs, deps=deps)

    async def invoke_async(self, *args: str, **kwargs: Unpack[RunnerArgs]):
        final_kwargs = self.coalesce_args(*args, **kwargs)
        deps = kwargs.get("deps") or self.deps
        return await cappa.invoke_async(**final_kwargs, deps=deps)
