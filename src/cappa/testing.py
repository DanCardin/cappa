from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TextIO, TypedDict

from typing_extensions import Unpack

import cappa
from cappa.base import Backend, CappaCapable, T
from cappa.help import HelpFormattable
from cappa.invoke import DepTypes
from cappa.state import State

__all__ = [
    "CommandRunner",
    "RunnerArgs",
]


class RunnerArgs(TypedDict, total=False):
    """Available kwargs for `parse` and `invoke` function, to match `CommandRunner` fields."""

    argv: list[str]
    backend: Backend | None
    output: cappa.Output | None
    color: bool
    version: str | cappa.Arg[str] | None
    help: bool | cappa.Arg[bool]
    completion: bool | cappa.Arg[bool]
    help_formatter: HelpFormattable | None
    input: TextIO | None
    state: State[Any] | None


@dataclass
class CommandRunner(Generic[T]):
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
        ...     second: str = "2"

        Create an instance with no arguments means there is no default state

        >>> runner = CommandRunner()
        >>> runner.parse(Obj, "one")
        Obj(first='one', second='2')

        Or create a runner that always uses the same base CLI object, and default base command

        >>> runner = CommandRunner(Obj, base_args=["first"])

        Now each test, can customize the behavior to suit the test in question.

        >>> runner.parse(color=False)
        Obj(first='first', second='2')

        >>> runner.parse("two")
        Obj(first='first', second='two')
    """

    obj: CappaCapable[T] | None = None
    deps: DepTypes = None
    backend: Backend | None = None
    output: cappa.Output | None = None
    color: bool = True
    version: str | cappa.Arg[str] | None = None
    help: bool | cappa.Arg[bool] = True
    completion: bool | cappa.Arg[bool] = True
    help_formatter: HelpFormattable | None = None
    input: TextIO | None = None
    state: State[Any] | None = None

    base_args: list[str] = field(default_factory=lambda: [])

    def coalesce_kwargs(self, *args: str, **kwargs: Unpack[RunnerArgs]) -> RunnerArgs:
        return RunnerArgs(
            argv=self.base_args + list(args),
            backend=kwargs.get("backend") or self.backend,
            output=kwargs.get("output") or self.output,
            color=kwargs.get("color") or self.color,
            version=kwargs.get("version") or self.version,
            help=kwargs["help"] if "help" in kwargs else self.help,
            completion=kwargs["completion"]
            if "completion" in kwargs
            else self.completion,
            help_formatter=kwargs.get("help_formatter") or self.help_formatter,
            input=kwargs.get("input") or self.input,
            state=kwargs.get("state") or self.state,
        )

    def collect_args(
        self, obj: CappaCapable[T] | str | None = None, *args: str
    ) -> tuple[CappaCapable[T], tuple[str, ...]]:
        if isinstance(obj, str):
            assert self.obj
            return self.obj, (obj, *args)

        obj = obj or self.obj
        assert obj
        return obj, args

    def parse(
        self,
        obj: CappaCapable[T] | str | None = None,
        *args: str,
        **kwargs: Unpack[RunnerArgs],
    ) -> T:
        obj, args = self.collect_args(obj, *args)
        final_kwargs = self.coalesce_kwargs(*args, **kwargs)
        return cappa.parse(obj, **final_kwargs)

    def invoke(
        self,
        obj: CappaCapable[T] | str | None = None,
        *args: str,
        deps: DepTypes = None,
        **kwargs: Unpack[RunnerArgs],
    ) -> Any:
        obj, args = self.collect_args(obj, *args)
        final_kwargs = self.coalesce_kwargs(*args, **kwargs)
        deps = deps or self.deps
        return cappa.invoke(obj, **final_kwargs, deps=deps)

    async def invoke_async(
        self,
        obj: CappaCapable[T] | str | None = None,
        *args: str,
        deps: DepTypes = None,
        **kwargs: Unpack[RunnerArgs],
    ) -> Any:
        obj, args = self.collect_args(obj, *args)
        final_kwargs = self.coalesce_kwargs(*args, **kwargs)
        deps = deps or self.deps
        return await cappa.invoke_async(obj, **final_kwargs, deps=deps)
