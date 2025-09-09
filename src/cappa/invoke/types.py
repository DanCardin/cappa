from __future__ import annotations

import contextlib
import inspect
from dataclasses import dataclass, field
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Coroutine,
    Generator,
    Generic,
    Mapping,
    Sequence,
    TypeVar,
    Union,
    cast,
)

from typing_extensions import Annotated

from cappa.output import Exit, Output
from cappa.type_view import Empty, EmptyType


class SelfType: ...


C = TypeVar("C")
T = TypeVar("T")
InvokeCallable = Callable[..., T]
InvokeCallableSpec = Union[InvokeCallable[T], str]


@dataclass(frozen=True)
class Dep(Generic[T]):
    """Describes the callable required to fulfill a given dependency."""

    callable: InvokeCallableSpec[T]


DepTypes = Union[
    Sequence[InvokeCallableSpec[Any]],
    Mapping[InvokeCallableSpec[Any], Union[Dep[Any], InvokeCallableSpec[Any], Any]],
    None,
]
Self = Annotated[T, SelfType]


class InvokeResolutionError(RuntimeError):
    """Raised for errors encountered during evaluation of invoke dependencies."""


@dataclass
class Resolved(Generic[C]):
    callable: InvokeCallableSpec[C]
    kwargs: dict[str, Any | Resolved[Any]] = field(default_factory=lambda: {})
    args: tuple[Any, ...] = field(default=())
    result: C | EmptyType = Empty

    def call(self, *args: Any, output: Output | None = None, managed: bool = True):
        with self.get(*args, output=output, managed=managed) as value:
            return value

    async def call_async(self, *args: Any, output: Output | None = None):
        async with self.get_async(*args, output=output) as value:
            return value

    @contextlib.contextmanager
    def get(
        self, *args: Any, output: Output | None = None, managed: bool = True
    ) -> Generator[C, None, None]:
        """Get the resolved value.

        The value itself is cached in the event it's used as a dependency to more
        than one dependency.
        """
        if self.result is not Empty:
            yield self.result
            return

        with contextlib.ExitStack() as stack:
            # Non-resolved values are literal values that can be recorded directly.
            finalized_kwargs = dict(self.iter_kwargs(is_resolved=False))

            # Resolved values need to be recursed into. In order to handle the
            # wrapping context manager, we need to enter all contexts, and only
            # exit at the end.
            for k, v in self.iter_kwargs(is_resolved=True):
                finalized_kwargs[k] = stack.enter_context(
                    v.get(output=output, managed=managed)
                )

            with self.handle_exit(output):
                callable = cast(Callable[..., Any], self.callable)
                requires_management = inspect.isgeneratorfunction(callable)
                if requires_management:
                    # Yield functions are assumed to be context-manager style generators
                    # that we just need to wrap...
                    callable = contextlib.contextmanager(callable)

                result: Any = callable(*args, *self.args, **finalized_kwargs)
                is_context_manager = isinstance(
                    result, contextlib.AbstractContextManager
                )

                # And then enter before producing the result.
                if requires_management or (managed and is_context_manager):
                    result = stack.enter_context(result)  # pyright: ignore

            self.result = result
            yield result

    @contextlib.asynccontextmanager
    async def get_async(
        self, *args: Any, output: Output | None = None
    ) -> AsyncGenerator[C, None]:
        """Get the resolved value, in an async context.

        Note, this is the exact same process as in `get`, except with `await`,
        `enter_async_context` and `async with`. There seems to be no way to
        share the logic between the two methods, so they just need to be kept
        in sync :shrug:.
        """
        if self.result is not Empty:
            yield self.result
            return

        async with contextlib.AsyncExitStack() as stack:
            finalized_kwargs = dict(self.iter_kwargs(is_resolved=False))
            for k, v in self.iter_kwargs(is_resolved=True):
                finalized_kwargs[k] = await stack.enter_async_context(
                    v.get_async(output=output)
                )

            with self.handle_exit(output):
                callable = cast(Callable[..., Any], self.callable)
                requires_management = inspect.isasyncgenfunction(callable)
                if requires_management:
                    callable = contextlib.asynccontextmanager(callable)

                result: Any = callable(*args, *self.args, **finalized_kwargs)
                is_context_manager = isinstance(
                    result, contextlib.AbstractAsyncContextManager
                )

                if requires_management or is_context_manager:
                    result = await stack.enter_async_context(result)  # pyright: ignore
                elif isinstance(result, Coroutine):
                    result = await result  # pyright: ignore

            self.result = result
            yield result

    def iter_kwargs(self, *, is_resolved: bool):
        for k, v in self.kwargs.items():
            if is_resolved == isinstance(v, self.__class__):
                yield k, v

    @classmethod
    @contextlib.contextmanager
    def handle_exit(cls, output: Output | None = None):
        try:
            yield
        except Exit as e:
            if output:  # pragma: no cover
                output.exit(e)
            raise e
