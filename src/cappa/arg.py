"""Define the external facing argument definition types provided by a user."""
from __future__ import annotations

import dataclasses
import enum
import typing
from collections.abc import Callable

from typing_inspect import is_optional_type

from cappa.annotation import (
    detect_choices,
    is_sequence_type,
    parse_optional,
    parse_value,
)
from cappa.class_inspect import Field, extract_dataclass_metadata
from cappa.completion.completers import complete_choices
from cappa.completion.types import Completion
from cappa.env import Env
from cappa.subcommand import Subcommand
from cappa.typing import (
    MISSING,
    NoneType,
    T,
    find_type_annotation,
    is_subclass,
    is_union_type,
    missing,
)


@enum.unique
class ArgAction(enum.Enum):
    """`Arg` action typee.

    Options:
      - set: Stores the given CLI value directly.
      - store_true: Stores a literal `True` value, causing options to not attempt to
        consume additional CLI arguments
      - store_false: Stores a literal `False` value, causing options to not attempt to
        consume additional CLI arguments
      - append: Produces a list, and accumulates the given value on top of prior values.
      - count: Increments an integer starting at 0
      - help: Cancels argument parsing and prints the help text
      - version: Cancels argument parsing and prints the CLI version
      - completion: Cancels argument parsing and enters "completion mode"
    """

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

    @classmethod
    def is_custom(cls, action: ArgAction | Callable | None):
        return action is not None and not isinstance(action, ArgAction)


@dataclasses.dataclass
class Arg(typing.Generic[T]):
    """Describe a CLI argument.

    Arguments:
        value_name: Placeholder for the argument's value in the help message / usage.
            Defaults to the name of the corresponding class field.
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

        field_name: The name of the class field to populate with this arg. In most usecases,
            this field should be left unspecified and automatically inferred.
    """

    value_name: str | MISSING = missing
    short: bool | str | list[str] = False
    long: bool | str | list[str] = False
    count: bool = False
    default: T | None | MISSING = missing
    help: str | None = None
    parse: Callable[[typing.Any], T] | None = None

    group: str | tuple[int, str] | MISSING = missing
    hidden: bool = False

    action: ArgAction | Callable | None = None
    num_args: int | None = None
    choices: list[str] | None = None
    completion: Callable[..., list[Completion]] | None = None

    required: bool | None = None

    field_name: str | MISSING = missing

    @classmethod
    def collect(
        cls, field: Field, type_hint: type, fallback_help: str | None = None
    ) -> Arg:
        object_annotation = find_type_annotation(type_hint, cls)
        annotation = object_annotation.annotation

        if object_annotation.obj is None:
            arg = cls()
        else:
            arg = typing.cast(Arg, object_annotation.obj)

        if object_annotation.doc:
            fallback_help = object_annotation.doc

        # Dataclass field metatdata takes precedence if it exists.
        field_metadata = extract_dataclass_metadata(field)
        assert not isinstance(field_metadata, Subcommand)

        if field_metadata:
            arg = field_metadata

        field_name = infer_field_name(arg, field)
        default = infer_default(arg, field, annotation)

        arg = dataclasses.replace(arg, field_name=field_name, default=default)
        return arg.normalize(annotation, fallback_help=fallback_help)

    def normalize(
        self,
        annotation: typing.Any = NoneType,
        fallback_help: str | None = None,
        action: ArgAction | Callable | None = None,
        default: typing.Any = missing,
        value_name: str | None = None,
        field_name: str | None = None,
    ) -> Arg:
        origin = typing.get_origin(annotation) or annotation
        type_args = typing.get_args(annotation)

        field_name = typing.cast(str, field_name or self.field_name)
        value_name = value_name or (
            self.value_name if self.value_name is not missing else field_name
        )
        default = default if default is not missing else self.default

        verify_type_compatibility(self, annotation, origin, type_args)
        short = infer_short(self, field_name)
        long = infer_long(self, origin, field_name)
        choices = infer_choices(self, origin, type_args)
        action = action or infer_action(self, origin, type_args, long, default)
        num_args = infer_num_args(self, origin, type_args, action, long)
        required = infer_required(self, annotation, default)

        parse = infer_parse(self, annotation)
        help = infer_help(self, choices, fallback_help)
        completion = infer_completion(self, choices)

        group = infer_group(self, short, long)

        return dataclasses.replace(
            self,
            default=default,
            field_name=field_name,
            value_name=value_name,
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

    def names(self, *, n=0) -> list[str]:
        short_names = typing.cast(list, self.short or [])
        long_names = typing.cast(list, self.long or [])
        result = short_names + long_names
        if n:
            return result[:n]
        return result

    def names_str(self, delimiter: str = ", ", *, n=0) -> str:
        if self.long or self.short:
            return delimiter.join(self.names(n=n))

        return typing.cast(str, self.value_name)


def verify_type_compatibility(
    arg: Arg, annotation: type, origin: type, type_args: tuple[type, ...]
):
    """Verify classes of annotations are compatible with one another.

    Thus far:
        * Sequence and scalar types should not be mixed, unless an explicit `parse`
          is provided. Otherwise, they will always result in sequence-type results
          which will not map correctly to scalar types.

        * num_args!=1 should only be used with sequence types.
        * ArgAction.append should only be used with sequence types.
    """
    action = arg.action
    if arg.parse or ArgAction.is_custom(action):
        return

    if is_union_type(origin):
        all_same_arity = {
            is_sequence_type(ta) for ta in type_args if ta is not NoneType
        }
        if len(all_same_arity) > 1:
            raise ValueError(
                f"On field '{arg.field_name}', apparent mismatch of annotated type with `Arg` options. "
                'Unioning "sequence" types with non-sequence types is not currently supported, '
                "unless using `Arg(parse=...)` or `Arg(action=<callable>)`. "
                "See [documentation](https://cappa.readthedocs.io/en/latest/annotation.html) for more details."
            )
        return

    num_args = arg.num_args
    if is_sequence_type(origin):
        if num_args == 1 or action not in {ArgAction.append, None}:
            raise ValueError(
                f"On field '{arg.field_name}', apparent mismatch of annotated type with `Arg` options. "
                f"'{annotation}' type produces a sequence, whereas `num_args=1`/`action={action}` do not. "
                "See [documentation](https://cappa.readthedocs.io/en/latest/annotation.html) for more details."
            )
    else:
        if num_args not in {None, 1} or action is ArgAction.append:
            raise ValueError(
                f"On field '{arg.field_name}', apparent mismatch of annotated type with `Arg` options. "
                f"'{origin.__name__}' type produces a scalar, whereas `num_args={num_args}`/`action={action}` do not. "
                "See [documentation](https://cappa.readthedocs.io/en/latest/annotation.html) for more details."
            )


def infer_field_name(arg: Arg, field: Field) -> str:
    if not isinstance(arg.field_name, MISSING):
        raise ValueError("Arg 'name' cannot be set when using automatic inference.")

    return field.name


def infer_default(arg: Arg, field: Field, annotation: type) -> typing.Any:
    if arg.default is not missing:
        # Annotated[str, Env('FOO')] = "bar" should produce "bar". I.e. the field default
        # should be used if the `Env` default is not set.
        if (
            isinstance(arg.default, Env)
            and arg.default.default is None
            and field.default is not missing
        ):
            return field.default

        return arg.default

    if field.default is not missing:
        return field.default

    if field.default_factory is not missing:
        return field.default_factory()

    if is_optional_type(annotation):
        return None

    if is_subclass(annotation, bool):
        return False

    return missing


def infer_required(arg: Arg, annotation: type, default: typing.Any | MISSING):
    if arg.required is True:
        return True

    if default is missing:
        if is_subclass(annotation, bool) or is_optional_type(annotation):
            return False

        if arg.required is False:
            raise ValueError(
                "When specifying `required=False`, a default value must be supplied able to be "
                "supplied through type inference, `Arg(default=...)`, or through class-level default"
            )

        return True

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

    return [item if item.startswith("-") else f"-{item[0]}" for item in short]


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
) -> ArgAction | Callable:
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
    unbounded_num_args = arg.num_args == -1

    if arg.parse or unbounded_num_args or (is_positional and not has_specific_num_args):
        return ArgAction.set

    if is_subclass(origin, (list, set)):
        return ArgAction.append

    if is_subclass(origin, tuple):
        is_unbounded_tuple = len(type_args) == 2 and type_args[1] == ...
        if is_unbounded_tuple:
            return ArgAction.append

    return ArgAction.set


def infer_num_args(
    arg: Arg,
    origin: typing.Any,
    type_args: tuple[type, ...],
    action: ArgAction | Callable,
    long,
) -> int | None:
    if arg.num_args is not None:
        return arg.num_args

    if arg.parse:
        return 1

    if isinstance(action, ArgAction) and action in no_extra_arg_actions:
        return 0

    if is_union_type(origin):
        # Recursively determine the `num_args` value of each variant. Use the value
        # only if they all result in the same value.
        distinct_num_args = set()
        num_args_variants = []
        for type_arg in type_args:
            type_origin = typing.get_origin(type_arg)

            num_args = infer_num_args(
                arg,
                type_origin,
                typing.get_args(type_arg),
                action,
                long,
            )

            distinct_num_args.add(num_args)
            num_args_variants.append((type_arg, num_args))

        # The ideal case, where all union variants have the same arity and can be unioned amongst.
        if len(distinct_num_args) == 1:
            return distinct_num_args.pop()

        invalid_kinds = ", ".join(
            [
                f"`{type_arg}` produces `num_args={n}`"
                for type_arg, n in num_args_variants
            ]
        )
        raise ValueError(
            f"On field '{arg.field_name}', mismatch of arity between union variants. {invalid_kinds}."
        )

    is_positional = not arg.short and not long
    if is_subclass(origin, (list, set)) and is_positional:
        return -1

    is_tuple = is_subclass(origin, tuple)
    is_unbounded_tuple = is_tuple and len(type_args) == 2 and type_args[1] == ...

    if is_tuple and not is_unbounded_tuple:
        return len(type_args)

    if is_unbounded_tuple and is_positional:
        return -1
    return 1


def infer_parse(arg: Arg, annotation: type) -> Callable:
    if arg.parse:
        if is_optional_type(annotation):
            return parse_optional(arg.parse)
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
