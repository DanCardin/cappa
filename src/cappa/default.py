from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable, ClassVar, Generic, TextIO, Union

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
        return cls().fallback(default)

    def fallback(self, other: DefaultTypes | Any) -> Default:
        cls = type(self)
        if isinstance(other, cls):
            return cls(*self.sequence, *other.sequence, default=other.default)

        if isinstance(other, default_types):
            default = self.default
            if self.default is Empty and isinstance(other, Env):
                default = other.default

            return cls(*self.sequence, other, default=default)

        return cls(*self.sequence, default=other)

    def __or__(self, other: DefaultTypes) -> Default:
        return self.fallback(other)

    def __call__(
        self, state: State | None = None, input: TextIO | None = None
    ) -> tuple[bool, Any | None]:
        for default in self.sequence:
            if isinstance(default, ValueFrom):
                value = default(state=state)
            elif isinstance(default, (Prompt, Confirm)):
                value = default(input=input)
            else:
                value = default()  # type: ignore

            if value is not Empty:
                return default.is_parsed, value

        if self.default is Empty:
            return True, None

        return True, self.default


class DefaultType:
    is_parsed: ClassVar[bool] = False

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
    default: str | None | EmptyType = Empty

    def __init__(
        self, env_var: str, *env_vars: str, default: str | None | EmptyType = Empty
    ):
        object.__setattr__(self, "env_vars", (env_var, *env_vars))
        object.__setattr__(self, "default", default)

    def __call__(self) -> str | None | EmptyType:
        for env_var in self.env_vars:
            value = os.getenv(env_var)
            if value is not None:
                return value

        return self.default


class Prompt(DefaultType, rich.prompt.Prompt):
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


class Confirm(DefaultType, rich.prompt.Confirm):
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

    callable: Callable
    kwargs: dict[str, Any]

    is_parsed: ClassVar[bool] = True

    def __init__(self, callable: Callable, **kwargs: Any):
        object.__setattr__(self, "callable", callable)
        object.__setattr__(self, "kwargs", kwargs)

    def __call__(self, state: State | None = None):
        from cappa.invoke import fulfill_deps

        kwargs = self.kwargs
        if state:
            deps = {State: state}
            resolved = fulfill_deps(self.callable, deps, allow_empty=True)
            kwargs = {**resolved.kwargs, **self.kwargs}

        return self.callable(**kwargs)


@dataclass
class DefaultFormatter(Generic[T]):
    format: str = "{default}"
    show: bool = True

    @classmethod
    def disabled(cls):
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
