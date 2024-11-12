"""Define the external facing argument definition types provided by a user."""

from __future__ import annotations

import dataclasses
import enum
import typing
from collections.abc import Callable
from functools import cached_property
from typing import Sequence, Union

from typing_extensions import TypeAlias

from cappa.class_inspect import Field, extract_dataclass_metadata
from cappa.completion.completers import complete_choices
from cappa.completion.types import Completion
from cappa.env import Env
from cappa.parse import evaluate_parse, parse_value
from cappa.type_view import Empty, EmptyType, TypeView
from cappa.typing import (
    Doc,
    T,
    detect_choices,
    find_annotations,
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

    @classmethod
    def is_non_value_consuming(cls, action: ArgAction | Callable | None):
        return action in {
            ArgAction.store_true,
            ArgAction.store_false,
            ArgAction.count,
            ArgAction.version,
            ArgAction.help,
        }

    @property
    def is_bool_action(self):
        return self in {self.store_true, self.store_false}


ArgActionType: TypeAlias = Union[ArgAction, Callable]


@dataclasses.dataclass(frozen=True)
class Group:
    """Object used to control argument/subcommand grouping in generated help text.

    Args:
        order: A number representing the relative ordering among different argument
            groups. Groups with the same order will be displayed alphabetically by
            name.
        name: The display name of the group in help text.
        exclusive: Whether arguments in the group should be considered mutually exclusive
            of one another.
        section: A secondary level of ordering. Sections have a higher order precedence
            than ``order``, in order to facilitate meta-ordering amongst kinds of groups
            (such as "meta" arguments (``--help``, ``--version``, etc) and subcommands).
            The default ``section`` for any normal argument/``Group`` is 0, for
            ``Subcommand``s it is 1, and for "meta" arguments it is 2.
    """

    order: int = dataclasses.field(default=0, compare=False)
    name: str = ""
    exclusive: bool = False
    section: int = 0

    @cached_property
    def key(self):
        return (self.section, self.order, self.name, self.exclusive)


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
            Note, if the default value is used, it will not be coerced into the annotated
            type through the `parse` method.
        help: By default, the help text will be inferred from the containing class'
            arguments' section, if it exists. Alternatively, you can directly supply
            the help text here.
        parse: An optional function which accepts the raw string argument as input and
            returns a parsed value type's instance. This should only be required for
            complex types that the type system's built-in parsing cannot handle.

        group: Optional group names for the argument. This affects how they're displayed
            in the backend's help text. Note this can also be a `Group` instance in order
            to control group order and/or group exclusivity.
        hidden: Whether the argument should be hidden in help text. Defaults to False.

        action: Generally automatically inferred from the data type. This allows to
            override the default.
        num_args: Generally automatically inferred from the data type. This allows to
            override the default.
        choices: Generally automatically inferred from the data type. This allows to
            override the default.
        completion: Used to provide custom completions. If specified, should be a function
            which accepts a partial string value and returns a list of
            [cappa.Completion](cappa.Completion) objects.
        required: Defaults to automatically inferring requiredness, based on whether the
            class's value has a default. By setting this, you can force a particular value.
        field_name: The name of the class field to populate with this arg. In most usecases,
            this field should be left unspecified and automatically inferred.
        deprecated: If supplied, the argument will be marked as deprecated. If given `True`,
            a default message will be generated, otherwise a supplied string will be
            used as the deprecation message.
        show_default: Whether to show the default value in help text. Defaults to `True`.
        destructured: When set, destructures the annotated type into current-level arguments.
            See `Arg.destructure`.
        has_value: Whether the argument has a value that should be saved back to the destination
            type. For most `Arg`, this will default to `True`, however `--help` is an example
            of an `Arg` for which it is false.
    """

    value_name: str | EmptyType = Empty
    short: bool | str | list[str] | None = False
    long: bool | str | list[str] | None = False
    count: bool = False
    default: T | None | EmptyType = Empty
    help: str | None = None
    parse: Callable[..., T] | Sequence[Callable[..., T]] | None = None

    group: str | tuple[int, str] | Group | EmptyType = Empty

    hidden: bool = False
    action: ArgActionType | None = None
    num_args: int | None = None
    choices: list[str] | None = None
    completion: Callable[..., list[Completion]] | None = None
    required: bool | None = None
    field_name: str | EmptyType = Empty
    deprecated: bool | str = False
    show_default: bool = True

    destructured: Destructured | None = None
    has_value: bool | None = None

    type_view: TypeView | None = None

    @classmethod
    def collect(
        cls,
        field: Field,
        type_view: TypeView,
        fallback_help: str | None = None,
        default_short: bool = False,
        default_long: bool = False,
    ) -> list[Arg]:
        args = find_annotations(type_view, cls) or [Arg()]

        exclusive = len(args) > 1

        docs = find_annotations(type_view, Doc)
        fallback_help = docs[0].documentation if docs else fallback_help

        # Dataclass field metadata takes precedence if it exists.
        field_metadata = extract_dataclass_metadata(field, Arg)
        if field_metadata:
            args = field_metadata

        result = []
        for arg in args:
            field_name = infer_field_name(arg, field)
            default = infer_default(arg, field, type_view)

            arg = dataclasses.replace(
                arg,
                field_name=field_name,
                default=default,
            )
            normalized_arg = arg.normalize(
                type_view,
                fallback_help=fallback_help,
                default_short=default_short,
                default_long=default_long,
                exclusive=exclusive,
            )

            if arg.destructured:
                destructured_args = destructure(normalized_arg, type_view)
                result.extend(destructured_args)
            else:
                result.append(normalized_arg)

        return list(explode_negated_bool_args(result))

    def normalize(
        self,
        type_view: TypeView | None = None,
        fallback_help: str | None = None,
        action: ArgActionType | None = None,
        default: typing.Any = Empty,
        field_name: str | None = None,
        default_short: bool = False,
        default_long: bool = False,
        exclusive: bool = False,
    ) -> Arg:
        if type_view is None:
            type_view = TypeView(typing.Any)

        field_name = typing.cast(str, field_name or self.field_name)
        default = default if default is not Empty else self.default

        verify_type_compatibility(self, field_name, type_view)
        short = infer_short(self, field_name, default_short)
        long = infer_long(self, type_view, field_name, default_long)
        choices = infer_choices(self, type_view)
        action = action or infer_action(self, type_view, long, default)
        num_args = infer_num_args(self, type_view, action, long)
        required = infer_required(self, type_view, default)

        parse = infer_parse(self, type_view)
        help = infer_help(self, fallback_help)
        completion = infer_completion(self, choices)

        group = infer_group(self, short, long, exclusive)

        value_name = infer_value_name(self, field_name, num_args)
        has_value = infer_has_value(self, action)

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
            has_value=has_value,
            type_view=type_view,
        )

    @classmethod
    def destructure(cls, settings: Destructured | None = None):
        return cls(destructured=settings or Destructured())

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


def verify_type_compatibility(arg: Arg, field_name: str, type_view: TypeView):
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

    if type_view.is_union:
        all_same_arity = {
            ta.is_subclass_of((list, tuple, set))
            for ta in type_view.strip_optional().inner_types
        }
        if len(all_same_arity) > 1:
            raise ValueError(
                f"On field '{field_name}', apparent mismatch of annotated type with `Arg` options. "
                'Unioning "sequence" types with non-sequence types is not currently supported, '
                "unless using `Arg(parse=...)` or `Arg(action=<callable>)`. "
                "See [documentation](https://cappa.readthedocs.io/en/latest/annotation.html) for more details."
            )
        return

    num_args = arg.num_args
    if type_view.is_subclass_of((list, tuple, set)):
        if num_args in {0, 1} and action not in {ArgAction.append, None}:
            raise ValueError(
                f"On field '{field_name}', apparent mismatch of annotated type with `Arg` options. "
                f"'{type_view.repr_type}' type produces a sequence, whereas `num_args=1`/`action={action}` do not. "
                "See [documentation](https://cappa.readthedocs.io/en/latest/annotation.html) for more details."
            )
    else:
        if num_args not in {None, 0, 1} or action is ArgAction.append:
            raise ValueError(
                f"On field '{field_name}', apparent mismatch of annotated type with `Arg` options. "
                f"'{type_view.repr_type}' type produces a scalar, whereas `num_args={num_args}`/`action={action}` do not. "
                "See [documentation](https://cappa.readthedocs.io/en/latest/annotation.html) for more details."
            )


def infer_field_name(arg: Arg, field: Field) -> str:
    if arg.field_name is not Empty:
        raise ValueError("Arg 'name' cannot be set when using automatic inference.")

    return field.name


def infer_default(arg: Arg, field: Field, type_view: TypeView) -> typing.Any:
    if arg.default is not Empty:
        # Annotated[str, Env('FOO')] = "bar" should produce "bar". I.e. the field default
        # should be used if the `Env` default is not set, but still attempt to read the
        # `Env` if it **is** set.
        if (
            isinstance(arg.default, Env)
            and arg.default.default is None
            and field.default is not Empty
        ):
            return Env(*arg.default.env_vars, default=field.default)

        return arg.default

    if field.default is not Empty:
        return field.default

    if field.default_factory is not Empty:
        return field.default_factory()

    if type_view.is_optional:
        return None

    if type_view.is_subclass_of(bool):
        return False

    return Empty


def infer_required(arg: Arg, type_view: TypeView, default: typing.Any | EmptyType):
    required = arg.required
    if required is True:
        return True

    if default is Empty:
        if required is False:
            raise ValueError(
                "When specifying `required=False`, a default value must be supplied able to be "
                "supplied through type inference, `Arg(default=...)`, or through class-level default"
            )

        return True

    return False


def infer_short(
    arg: Arg, name: str, default: bool = False
) -> list[str] | typing.Literal[False]:
    short = arg.short or default
    if not short:
        return False

    if isinstance(short, bool):
        short_name = name[0]
        return [f"-{short_name}"]

    if isinstance(short, str):
        short = short.split("/")
    else:
        short = short

    return [item if item.startswith("-") else f"-{item}" for item in short]


def infer_long(
    arg: Arg, type_view: TypeView, name: str, default: bool
) -> list[str] | typing.Literal[False]:
    long = arg.long or default

    if not long:
        # bools get automatically coerced into flags, otherwise stay off.
        if not type_view.is_subclass_of(bool):
            return False

        long = True

    if isinstance(long, bool):
        long = name.replace("_", "-")
        return [f"--{long}"]

    if isinstance(long, str):
        long = long.split("/")

    return [item if item.startswith("--") else f"--{item}" for item in long]


def infer_choices(arg: Arg, type_view: TypeView) -> list[str] | None:
    if arg.choices is None:
        choices = detect_choices(type_view)
    else:
        choices = arg.choices

    if not choices:
        return None

    return [str(c) for c in choices]


def infer_action(
    arg: Arg, type_view: TypeView, long, default: typing.Any
) -> ArgActionType:
    if arg.count:
        return ArgAction.count

    if arg.action is not None:
        return arg.action

    type_view = type_view.strip_optional()

    # Coerce raw `bool` into flags by default
    if type_view.is_subclass_of(bool):
        if isinstance(default, Env):
            default = default.default

        if default is not Empty and bool(default):
            return ArgAction.store_false

        return ArgAction.store_true

    is_positional = not arg.short and not long
    has_specific_num_args = arg.num_args is not None
    unbounded_num_args = arg.num_args == -1

    if (
        arg.parse
        or unbounded_num_args
        or (is_positional and not has_specific_num_args)
        or (has_specific_num_args and arg.num_args != 1)
    ):
        return ArgAction.set

    if type_view.is_subtype_of((list, set)):
        return ArgAction.append

    if type_view.is_variadic_tuple:
        return ArgAction.append

    return ArgAction.set


def infer_num_args(
    arg: Arg,
    type_view: TypeView,
    action: ArgActionType,
    long,
) -> int:
    if arg.num_args is not None:
        return arg.num_args

    if arg.parse:
        return 1

    if ArgAction.is_non_value_consuming(action):
        return 0

    if type_view.is_union:
        # Recursively determine the `num_args` value of each variant. Use the value
        # only if they all result in the same value.
        distinct_num_args = set()
        num_args_variants = []
        for type_arg in type_view.inner_types:
            if type_arg.is_none_type:
                continue

            num_args = infer_num_args(
                arg,
                type_arg,
                action,
                long,
            )

            distinct_num_args.add(num_args)
            num_args_variants.append((type_arg.raw, num_args))

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
    if type_view.is_subclass_of((list, set)) and is_positional:
        return -1

    if type_view.is_tuple and not type_view.is_variadic_tuple:
        return len(type_view.args)

    if type_view.is_variadic_tuple and is_positional:
        return -1
    return 1


def infer_parse(arg: Arg, type_view: TypeView) -> Callable:
    if arg.parse:
        parse = arg.parse
    else:
        parse = parse_value(type_view)

    return evaluate_parse(parse, type_view)


def infer_help(arg: Arg, fallback_help: str | None) -> str | None:
    help = arg.help
    if help is None:
        help = fallback_help

    return help


def infer_completion(
    arg: Arg, choices: list[str] | None
) -> Callable[[str], list[Completion]] | None:
    if arg.completion:
        return arg.completion

    if choices:
        return complete_choices(choices, help=arg.help)

    return None


def infer_group(
    arg: Arg, short: list[str] | bool, long: list[str] | bool, exclusive: bool = False
) -> Group:
    order = 0
    name = None
    section = 0

    if isinstance(arg.group, Group):
        name = arg.group.name
        order = arg.group.order
        exclusive = arg.group.exclusive
        section = arg.group.section

    if isinstance(arg.group, str):
        name = arg.group

    if isinstance(arg.group, tuple):
        order, name = arg.group

    if name is None:
        if short or long:
            name = "Options"
        else:
            name = "Arguments"
            order = 1

    return Group(name=name, order=order, exclusive=exclusive, section=section)


def infer_value_name(arg: Arg, field_name: str, num_args: int | None) -> str:
    if arg.value_name is not Empty:
        return arg.value_name

    if num_args == -1:
        return f"{field_name} ..."

    if num_args and num_args > 1:
        return " ".join([field_name] * num_args)

    return field_name


def explode_negated_bool_args(args: typing.Sequence[Arg]) -> typing.Iterable[Arg]:
    """Expand `--foo/--no-foo` solo arguments into dual-arguments.

    Acts as a transform from `Arg(long='--foo/--no-foo')` to
    `Annotated[Arg(long='--foo', action=ArgAction.store_true), Arg(long='--no-foo', action=ArgAction.store_false)]`
    """
    for arg in args:
        yielded = False
        if isinstance(arg.action, ArgAction) and arg.action.is_bool_action and arg.long:
            long = typing.cast(typing.List[str], arg.long)

            negatives = [item for item in long if "--no-" in item]
            positives = [item for item in long if "--no-" not in item]
            if negatives and positives:
                positive_arg = dataclasses.replace(
                    arg,
                    long=positives,
                    action=ArgAction.store_true,
                    show_default=arg.default is True,
                )
                negative_arg = dataclasses.replace(
                    arg,
                    long=negatives,
                    action=ArgAction.store_false,
                    show_default=arg.default is False,
                )

                yield positive_arg
                yield negative_arg
                yielded = True

        if not yielded:
            yield arg


def infer_has_value(arg: Arg, action: ArgActionType):
    if arg.has_value is not None:
        return arg.has_value

    if isinstance(action, ArgAction) and action in ArgAction.value_actions():
        return False

    return True


from cappa.destructure import Destructured, destructure  # noqa: E402
