"""Define the external facing argument definition types provided by a user."""
from __future__ import annotations

import dataclasses
import enum
import typing
from collections.abc import Callable
from typing import Generic

from typing_extensions import Self
from typing_inspect import is_optional_type, is_union_type

from cappa.annotation import detect_choices, parse_value
from cappa.class_inspect import Field, extract_dataclass_metadata
from cappa.subcommand import Subcommand
from cappa.typing import MISSING, T, find_type_annotation, is_subclass, missing


@enum.unique
class ArgAction(enum.Enum):
    set = "store"
    store_true = "store_true"
    store_false = "store_false"
    append = "append"
    count = "count"


@dataclasses.dataclass
class Arg(Generic[T]):
    """Describe a CLI argument.

    Arguments:
        name: The name of the argument. Defaults to the name of the corresponding class field.
        short: If `True`, uses first letter of the name to infer a (ex. `-s`) short
            flag. If a string is supplied, that will be used instead.
        long: If `True`, uses first letter of the name to infer a (ex. `--long`) long
            flag. If a string is supplied, that will be used instead.
        count: If `True` the resultant argmuent will count instances and accept zero
            arguments.
        default: An explicit default CLI value. When left unspecified, the default is
            inferred from the class' default or the adapter default/default_factory.
        help: By default, the help text will be inferred from the containing class'
            arguments' section, if it exists. Alternatively, you can directly supply
            the help text here.
        parse: An optional function which accepts the raw string argument as input and
            returns a parsed value type's instance. This should only be required for
            complex types that the type system's built-in parsing cannot handle.

        action: Generally automatically inferred from the data type. This allows to
            override the default.
        num_args: Generally automatically inferred from the data type. This allows to
            override the default.
        choices: Generally automatically inferred from the data type. This allows to
            override the default.

        required: Defaults to automatically inferring requiredness, based on whether the
            class's value has a default. By setting this, you can force a particular value.
    """

    name: str | MISSING = missing
    short: bool | str = False
    long: bool | str = False
    count: bool = False
    default: T | None | MISSING = ...
    help: str | None = None
    parse: Callable[[typing.Any], T] | None = None

    action: ArgAction = ArgAction.set
    num_args: int | None = None
    choices: list[str] | None = None

    required: bool | None = None

    @classmethod
    def collect(
        cls, field: Field, type_hint: type, fallback_help: str | None = None
    ) -> Self:
        arg, annotation = find_type_annotation(type_hint, cls)
        origin = typing.get_origin(annotation) or annotation
        type_args = typing.get_args(annotation)

        if arg is None:
            arg = cls()

        # Dataclass field metatdata takes precedence if it exists.
        field_metadata = extract_dataclass_metadata(field)
        assert not isinstance(field_metadata, Subcommand)

        if field_metadata:
            arg = field_metadata  # type: ignore

        kwargs: dict[str, typing.Any] = {}

        default = arg.default
        if arg.default is missing:
            if field.default is not missing:
                default = field.default

            if field.default_factory is not missing:
                default = field.default_factory()

        if arg.required is None and default is missing:
            kwargs["required"] = not is_optional_type(annotation)

        name: str = (
            field.name if isinstance(arg.name, MISSING) else typing.cast(str, arg.name)
        )
        kwargs["default"] = default
        kwargs["name"] = name

        if arg.short:
            kwargs["short"] = coerce_short_name(arg, name)

        long = arg.long

        # Coerce raw `bool` into flags by default
        if not is_union_type(origin):
            if is_subclass(origin, bool):
                if not long:
                    long = True

                kwargs["action"] = ArgAction.store_true

        is_positional = not arg.short and not long

        if arg.parse is None and not is_union_type(origin):
            if is_subclass(origin, (list, set)):
                if is_positional and arg.num_args is None:
                    kwargs["num_args"] = -1
                else:
                    kwargs["action"] = ArgAction.append

            if is_subclass(origin, tuple):
                if len(type_args) == 2 and type_args[1] == ...:
                    if is_positional and arg.num_args is None:
                        kwargs["num_args"] = -1
                    else:
                        kwargs["action"] = ArgAction.append
                else:
                    kwargs["num_args"] = len(type_args)

        choices = arg.choices or detect_choices(origin, type_args)
        if choices:
            kwargs["choices"] = choices

        if long:
            kwargs["long"] = coerce_long_name(arg, name)

        if arg.parse is None:
            kwargs["parse"] = parse_value(annotation)

        if arg.help is None:
            kwargs["help"] = fallback_help

        return dataclasses.replace(arg, **kwargs)


def coerce_short_name(arg: Arg, name: str) -> str:
    short = arg.short
    if isinstance(short, bool):
        short_name = name[0]
        return f"-{short_name}"

    if not short.startswith("-"):
        return f"-{short}"

    return short


def coerce_long_name(arg: Arg, name: str) -> str:
    long = arg.long
    if isinstance(long, bool):
        long = name.replace("_", "-")
        return f"--{long}"

    if not long.startswith("--"):
        return f"--{long}"
    return long
