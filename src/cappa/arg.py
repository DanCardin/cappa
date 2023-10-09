"""Define the external facing argument definition types provided by a user."""
from __future__ import annotations

import dataclasses
import enum
import typing
from collections.abc import Callable

from typing_inspect import is_optional_type

from cappa.annotation import detect_choices, parse_value
from cappa.class_inspect import Field, extract_dataclass_metadata
from cappa.completion.completers import complete_choices
from cappa.completion.types import Completion
from cappa.subcommand import Subcommand
from cappa.typing import (
    MISSING,
    NoneType,
    T,
    find_type_annotation,
    is_subclass,
    missing,
)


@enum.unique
class ArgAction(enum.Enum):
    set = "store"
    store_true = "store_true"
    store_false = "store_false"
    append = "append"
    count = "count"

    help = "help"
    version = "version"
    completion = "completion"

    @classmethod
    def value_actions(cls) -> typing.Set[ArgAction]:
        return {cls.help, cls.version, cls.completion}


@dataclasses.dataclass
class Arg(typing.Generic[T]):
    """Describe a CLI argument.

    Arguments:
        name: The name of the argument. Defaults to the name of the corresponding class field.
        short: If `True`, uses first letter of the name to infer a (ex. `-s`) short
            flag. If a string is supplied, that will be used instead. If a string is supplied,
            it is split on '/' (forward slash), to support multiple options. Additionally
            accepts a list of strings.
        long: If `True`, uses first letter of the name to infer a (ex. `--long`) long
            flag. If a string is supplied, that will be used instead. If a string is supplied,
            it is split on '/' (forward slash), to support multiple options. Additionally
            accepts a list of strings.
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

        group: Optional group names for the argument. This affects how they're displayed
            in the backended help text.
        hidden: Whether the argument should be hidden in help text. Defaults to False.

        action: Generally automatically inferred from the data type. This allows to
            override the default.
        num_args: Generally automatically inferred from the data type. This allows to
            override the default.
        choices: Generally automatically inferred from the data type. This allows to
            override the default.
        completion: Used to provide custom completions. If specified, should be a function
            which acccepts a partial string value and returns a list of
            [cappa.Completion](cappa.Completion) objects.

        required: Defaults to automatically inferring requiredness, based on whether the
            class's value has a default. By setting this, you can force a particular value.
    """

    name: str | MISSING = missing
    short: bool | str | list[str] = False
    long: bool | str | list[str] = False
    count: bool = False
    default: T | None | MISSING = missing
    help: str | None = None
    parse: Callable[[typing.Any], T] | None = None

    group: str | tuple[int, str] | MISSING = missing
    hidden: bool = False

    action: ArgAction | None = None
    num_args: int | None = None
    choices: list[str] | None = None
    completion: Callable[..., list[Completion]] | None = None

    required: bool | None = None

    @classmethod
    def collect(
        cls, field: Field, type_hint: type, fallback_help: str | None = None
    ) -> Arg:
        maybe_arg, annotation = find_type_annotation(type_hint, cls)

        if maybe_arg is None:
            maybe_arg = cls()

        arg = typing.cast(Arg, maybe_arg)

        # Dataclass field metatdata takes precedence if it exists.
        field_metadata = extract_dataclass_metadata(field)
        assert not isinstance(field_metadata, Subcommand)

        if field_metadata:
            arg = field_metadata

        name = infer_name(arg, field)
        default = infer_default(arg, field)

        arg = dataclasses.replace(arg, name=name, default=default)
        return arg.normalize(annotation, fallback_help)

    def normalize(
        self,
        annotation=NoneType,
        fallback_help: str | None = None,
        action: ArgAction | None = None,
        name: str | None = None,
    ) -> Arg:
        origin = typing.get_origin(annotation) or annotation
        type_args = typing.get_args(annotation)
        required = infer_required(self, annotation, self.default)

        name = typing.cast(str, name or self.name)
        short = infer_short(self, name)
        long = infer_long(self, origin, name)
        choices = infer_choices(self, origin, type_args)
        action = action or infer_action(self, origin, type_args, long, self.default)
        num_args = infer_num_args(self, origin, type_args, long)

        parse = infer_parse(self, annotation)
        help = infer_help(self, choices, fallback_help)
        completion = infer_completion(self, choices)

        group = infer_group(self, short, long)

        return dataclasses.replace(
            self,
            name=name,
            required=required,
            short=short,
            long=long,
            choices=choices,
            action=action,
            num_args=num_args,
            parse=parse,
            help=help,
            completion=completion,
            group=group,
        )

    def names(self) -> list[str]:
        short_names = typing.cast(list, self.short or [])
        long_names = typing.cast(list, self.long or [])
        return short_names + long_names

    def names_str(self, delimiter: str = ", ") -> str:
        if self.long or self.short:
            return delimiter.join(self.names())

        return typing.cast(str, self.name)


def infer_name(arg: Arg, field: Field) -> str:
    if not isinstance(arg.name, MISSING):
        raise ValueError("Arg 'name' cannot be set when using automatic inference.")

    return field.name


def infer_default(arg: Arg, field: Field) -> typing.Any:
    if arg.default is not missing:
        return arg.default

    if field.default is not missing:
        return field.default

    if field.default_factory is not missing:
        return field.default_factory()

    return missing


def infer_required(arg: Arg, annotation: type, default: typing.Any | MISSING):
    if arg.required is not None:
        return arg.required

    if default is missing:
        if is_subclass(annotation, bool):
            return False

        return not is_optional_type(annotation)

    return False


def infer_short(arg: Arg, name: str) -> list[str] | typing.Literal[False]:
    if not arg.short:
        return False

    if isinstance(arg.short, bool):
        short_name = name[0]
        return [f"-{short_name}"]

    if isinstance(arg.short, str):
        short = arg.short.split("/")
    else:
        short = arg.short

    return [item[:2] if item.startswith("-") else f"-{item[0]}" for item in short]


def infer_long(arg: Arg, origin: type, name: str) -> list[str] | typing.Literal[False]:
    long = arg.long

    if not long:
        # bools get automatically coerced into flags, otherwise stay off.
        if not is_subclass(origin, bool):
            return False

        long = True

    if isinstance(long, bool):
        long = name.replace("_", "-")
        return [f"--{long}"]

    if isinstance(long, str):
        long = long.split("/")

    return [item if item.startswith("--") else f"--{item}" for item in long]


def infer_choices(
    arg: Arg, origin: type, type_args: tuple[type, ...]
) -> list[str] | None:
    if arg.choices is None:
        choices = detect_choices(origin, type_args)
    else:
        choices = arg.choices

    if not choices:
        return None

    return [str(c) for c in choices]


def infer_action(
    arg: Arg, origin: type, type_args: tuple[type, ...], long, default: typing.Any
) -> ArgAction:
    if arg.count:
        return ArgAction.count

    if arg.action is not None:
        return arg.action

    # Coerce raw `bool` into flags by default
    if is_subclass(origin, bool):
        if default is not missing and bool(default):
            return ArgAction.store_false

        return ArgAction.store_true

    is_positional = not arg.short and not long
    has_specific_num_args = arg.num_args is not None

    if arg.parse or (is_positional and not has_specific_num_args):
        return ArgAction.set

    if is_subclass(origin, (list, set)):
        return ArgAction.append

    if is_subclass(origin, tuple):
        is_unbounded_tuple = len(type_args) == 2 and type_args[1] == ...
        if is_unbounded_tuple:
            return ArgAction.append

    return ArgAction.set


def infer_num_args(
    arg: Arg, origin: type, type_args: tuple[type, ...], long
) -> int | None:
    if arg.num_args is not None or arg.parse:
        return arg.num_args

    is_positional = not arg.short and not long

    if is_subclass(origin, (list, set)) and is_positional:
        return -1

    if is_subclass(origin, tuple):
        is_unbounded_tuple = len(type_args) == 2 and type_args[1] == ...
        if not is_unbounded_tuple:
            return len(type_args)

        if is_positional:
            return -1

    if is_subclass(origin, bool):
        return 1

    return None


def infer_parse(arg: Arg, annotation: type) -> Callable:
    if arg.parse:
        return arg.parse

    return parse_value(annotation)


def infer_help(
    arg: Arg, choices: list[str] | None, fallback_help: str | None
) -> str | None:
    help = arg.help
    if help is None:
        help = fallback_help

    if not choices:
        return help

    choices_str = "Valid options: " + ", ".join(choices) + "."

    if help:
        return f"{help} {choices_str}"

    return choices_str


def infer_completion(
    arg: Arg, choices: list[str] | None
) -> Callable[[str], list[Completion]] | None:
    if arg.completion:
        return arg.completion

    if choices:
        return complete_choices(choices, help=arg.help)

    return None


def infer_group(
    arg: Arg, short: list[str] | bool, long: list[str] | bool
) -> str | tuple[int, str]:
    group = arg.group
    group_name = None
    if isinstance(group, str):
        group_name = group
        group = missing

    if group is missing:
        if short or long:
            return (0, group_name or "Options")

        return (1, group_name or "Arguments")

    return typing.cast(typing.Tuple[int, str], group)


no_extra_arg_actions = {
    ArgAction.store_true,
    ArgAction.store_false,
    ArgAction.count,
    ArgAction.version,
    ArgAction.help,
}
