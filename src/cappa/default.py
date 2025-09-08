from __future__ import annotations

import os
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    ClassVar,
    Hashable,
    Protocol,
    TextIO,
    Union,
    runtime_checkable,
)

import rich.prompt
from typing_extensions import Self, TypeAlias, TypeVar

from cappa.state import State
from cappa.type_view import Empty, EmptyType

T = TypeVar("T")


@dataclass(frozen=True)
class Default:
    """Represents the sequence of fallback methods of default value retrieval for an `Arg`.

    **All** argument defaults (including static values) are coerced into `Default` instance.

    When evaluated for an argument, the provided sequence of default retrieval methods
    are evaluated in order, returning the value of the first option to return a non-None value.
    The `Default.default` value is returned if none of the provided methods return a value.

    Examples:
    - `Arg(default=4) == Arg(default=Default(default=4))`
    - `Arg(default=Env("FOO")) == Arg(default=Default(Env("FOO")))`
    - `Arg(default=Env("FOO") | Env("BAR")) == Arg(default=Default(Env("FOO"), Env("BAR")))`
    """

    sequence: tuple[DefaultType, ...] = ()
    default: EmptyType | Any = Empty

    def __init__(self, *sequence: DefaultTypes, default: Any = Empty):
        object.__setattr__(self, "sequence", sequence)
        object.__setattr__(self, "default", default)

    @classmethod
    def from_value(cls, default: Any) -> Default:
        """Produce a `Default` instance where the provided value is an explicit default.

        A default produced this way will resolve to a `Value` which gets appended to the
        fallback sequence rather than being overwriting the Default-level static fallback.

        Essentially `Default(..., Value(4), default=5)` will **always** evaluate to `4` if
        upstream fallbacks do not provide a value, and `5` will never be used. In practice
        this is utilized when `Arg(default=4)` is provided.

        This is distinct but similar to `Default() | 4 | 5` (which uses `fallback_to`), which
        would resolve to `Default((), default=5)`, the 4 being overwritten and never used.
        """
        return cls().fallback_to(default, explicit=True)

    @classmethod
    def fallback_from(cls, *defaults: Default | EmptyType | Any | None) -> Default:
        """Return a `Default` instance from a sequence of potential defaults.

        This is used to compose different levels of default sources (Arg.default versus
        normalization time defaults).
        """
        for default in defaults:
            if default is not Empty:
                return Default.from_value(default)

        return cls()

    def fallback_to(self, other: DefaultTypes | Any, explicit: bool = False) -> Default:
        """Produce a new Default from the current default and a supplied alternative.

        Examples:
            >>> Default(Env("FOO")).fallback_to(5)
            Default(sequence=(Env(env_vars=('FOO',), ...),), default=5)

            >>> Default(Env("FOO")).fallback_to(5, explicit=True)
            Default(sequence=(Env(env_vars=('FOO',), ...), Value(value=5)), default=<_EmptyEnum.EMPTY: 0>)
        """
        cls = type(self)
        if isinstance(other, cls):
            return cls(*self.sequence, *other.sequence, default=other.default)

        if isinstance(other, default_types):
            default = self.default
            if self.default is Empty and isinstance(other, Env):
                default = other.default

            if isinstance(other, PromptType):
                other = Prompt.from_prompt(other)

            if isinstance(other, ConfirmType):
                other = Confirm.from_confirm(other)

            return cls(*self.sequence, other, default=default)

        if explicit:
            return cls(*self.sequence, Value(other))

        return cls(*self.sequence, default=other)

    def __or__(self, other: Any) -> Default:
        """Compose two potential defaults, returning a new one.

        For example, `Default() | Prompt('...') | Env('FOO') | 5`. See `fallback_to` for details.
        """
        return self.fallback_to(other)

    def __call__(
        self, state: State[Any] | None = None, input: TextIO | None = None
    ) -> tuple[bool, Any | None]:
        """Evaluate the default retrieval sequence, returning the first non-Empty value."""
        for default in self.sequence:
            if isinstance(default, ValueFrom):
                value = default(state=state)
            elif isinstance(default, (Prompt, Confirm)):
                value = default(input=input)
            else:
                value = default()

            if value is not Empty:
                return default.is_parsed, value

        if self.default is Empty:
            return True, None

        return True, self.default

    @property
    def has_value(self) -> bool:
        """Whether the default instance **has** a default or if it's Empty."""
        return not self.sequence and self.default is Empty


@runtime_checkable
class DefaultType(Protocol):
    is_parsed: ClassVar[bool] = False

    def __call__(self, *_: Any, **__: Any) -> Any: ...  # pragma: no cover

    def __or__(self, other: DefaultTypes) -> Default:
        return Default(self) | other


@dataclass(frozen=True)
class Env(DefaultType):
    """Lazily evaluates environment variables in the order given.

    Argument value interpolation will handle and `Arg`'s default being an `Env`
    instance, by evaluating the `Env`, in the event the parser-level value
    fell back to the default.

    Examples:
        >>> from cappa import Arg, Env
        >>> arg = Arg(default=Env("HOST", "HOSTNAME", default="localhost"))
    """

    env_vars: tuple[str, ...]
    default: str | EmptyType | None = Empty

    def __init__(
        self, env_var: str, *env_vars: str, default: str | EmptyType | None = Empty
    ):
        object.__setattr__(self, "env_vars", (env_var, *env_vars))
        object.__setattr__(self, "default", default)

    def __call__(self) -> str | EmptyType | None:
        for env_var in self.env_vars:
            value = os.getenv(env_var)
            if value is not None:
                return value

        if self.default is None:
            return Empty
        return self.default


class Prompt(rich.prompt.Prompt, DefaultType):
    """Prompt the user for a value, returning the response.

    Examples:
        >>> from cappa import Arg, Prompt
        >>> arg = Arg(default=Prompt("Ask user for value"))
    """

    @classmethod
    def from_prompt(cls, prompt: Prompt | PromptType) -> Self:
        if isinstance(prompt, cls):
            return prompt
        return cls(
            console=prompt.console,
            prompt=prompt.prompt,
            password=prompt.password,
            choices=prompt.choices,
            show_default=prompt.show_default,
            show_choices=prompt.show_choices,
        )

    def __call__(self, input: TextIO | None = None):  # type: ignore
        return super().__call__(default=Empty, stream=input)


class Confirm(rich.prompt.Confirm, DefaultType):
    """Prompt the user for a confirmation, returning `True`/`False`.

    Examples:
        >>> from cappa import Arg, Confirm
        >>> arg = Arg(default=Confirm("Confirm with user"))
    """

    @classmethod
    def from_confirm(cls, confirm: Confirm | ConfirmType) -> Self:
        if isinstance(confirm, cls):
            return confirm
        return cls(
            console=confirm.console,
            prompt=confirm.prompt,
            password=confirm.password,
            choices=confirm.choices,
            show_default=confirm.show_default,
            show_choices=confirm.show_choices,
        )

    def __call__(self, input: TextIO | None = None):  # type: ignore
        return super().__call__(default=Empty, stream=input)


@dataclass(frozen=True)
class Value(DefaultType):
    value: Any

    is_parsed: ClassVar[bool] = True

    def __call__(self, state: State[Any] | None = None):
        return self.value


@dataclass(frozen=True)
class ValueFrom(DefaultType):
    """Retrieve the default value by calling the provided function.

    Optionally, `*args` and `**kwargs` to the supplied function can be
    provided ahead of time, to be supplied in the event the function is called.

    Examples:
        >>> from cappa import Arg, ValueFrom
        >>> def from_file(name):
        ...     with open(name) as f:
        ...         return f.read()
        >>>
        >>> arg = Arg(default=ValueFrom(from_file, name="config.json"))
    """

    callable: Callable[..., Any]
    kwargs: dict[str, Any]

    is_parsed: ClassVar[bool] = True

    def __init__(self, callable: Callable[..., Any], **kwargs: Any):
        object.__setattr__(self, "callable", callable)
        object.__setattr__(self, "kwargs", kwargs)

    def __call__(self, state: State[Any] | None = None):
        from cappa.invoke import fulfill_deps

        kwargs = self.kwargs
        if state:
            deps: dict[Hashable, Any] = {State: state}
            resolved = fulfill_deps(self.callable, deps, allow_empty=True)
            kwargs = {**resolved.kwargs, **self.kwargs}

        return self.callable(**kwargs)


@dataclass
class DefaultFormatter:
    format: str = "{default}"
    show: bool = True

    @classmethod
    def disabled(cls) -> Self:
        return cls(show=False)

    @classmethod
    def from_unknown(cls, value: str | bool | Self) -> Self:
        if isinstance(value, cls):
            return value

        if isinstance(value, str):
            return cls(format=value)

        return cls(show=bool(value))

    def format_default(self, default: Default, default_format: str = "") -> str:
        if not self.show:
            return ""

        default_raw_value = default.default
        if default_raw_value in (None, Empty):
            default_raw_value = ""

        default_formatted_value = self.format.format(default=default_raw_value)
        if default_formatted_value == "":
            return default_formatted_value

        return default_format.format(default=default_formatted_value)


PromptType = rich.prompt.Prompt
ConfirmType = rich.prompt.Confirm
default_types = (rich.prompt.Prompt, rich.prompt.Confirm, Env, ValueFrom)
DefaultTypes: TypeAlias = Union[
    Default, DefaultType, rich.prompt.Prompt, rich.prompt.Confirm
]
