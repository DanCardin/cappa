from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any, Iterable, TextIO

from typing_extensions import Annotated, Self, TypeAlias

from cappa.arg import Group
from cappa.class_inspect import Field, extract_dataclass_metadata
from cappa.completion.types import Completion
from cappa.invoke.types import Resolved
from cappa.state import State
from cappa.type_view import Empty, EmptyType, TypeView
from cappa.typing import T, assert_type, find_annotations

if TYPE_CHECKING:
    from cappa.arg import Arg
    from cappa.command import Alias, Command
    from cappa.help import HelpFormattable
    from cappa.output import Output


DEFAULT_SUBCOMMAND_GROUP = Group(3, "Subcommands", section=1)


@dataclasses.dataclass
class Subcommand:
    """Describe a CLI subcommand.

    Arguments:
        field_name: Defaults to the name of the class, converted to dash case, but
            can be overridden here.
        required: Defaults to automatically inferring requiredness, based on whether the
            class's value has a default. By setting this, you can force a particular value.
        group: The subcommand group, for use in controlling help text for the subcommand, and
            where it is displayed. This can be any of: the string name (``'Subcommands'``),
            a 2-tuple of the `order` and the name (``(3, "Subcommands")``), or a :class:`Group`
            instance (``Group(3, 'Subcommands')``)
        hidden: Whether the argument should be hidden in help text. Defaults to False.
        options: A mapping of the subcommand names to the corresponding `Command` to which
            the subcommands refer. Unless imperatively constructing the CLI structure, this
            field should generally always be inferred automatically.
        types: Defaults to the class's annotated types, but can be overridden here.
    """

    field_name: str | EmptyType = Empty
    required: bool | None = None
    group: str | tuple[int, str] | Group = DEFAULT_SUBCOMMAND_GROUP
    hidden: bool = False

    options: dict[str, Command[Any]] = dataclasses.field(default_factory=lambda: {})
    types: Iterable[type] | EmptyType = Empty

    # Mapping of alias name -> (canonical name in `options`, Alias metadata).
    # Populated during `normalize` from each Command's `aliases` field; collisions raise.
    alias_map: dict[str, tuple[str, Alias]] = dataclasses.field(
        default_factory=lambda: {}
    )

    @classmethod
    def detect(cls, field: Field, type_view: TypeView[Any]) -> Subcommand | None:
        subcommands = find_annotations(type_view, Subcommand) or None

        field_metadata = extract_dataclass_metadata(field, Subcommand)
        if field_metadata:
            subcommands = field_metadata

        if not subcommands:
            return None

        assert len(subcommands) == 1
        return subcommands[0]

    def normalize(
        self,
        type_view: TypeView[Any] | None = None,
        field_name: str | None = None,
        help_formatter: HelpFormattable | None = None,
        propagated_arguments: list[Arg[Any]] | None = None,
        state: State[Any] | None = None,
    ) -> Self:
        if type_view is None:
            type_view = TypeView(Any)

        field_name = field_name or assert_type(self.field_name, str)
        types = infer_types(self, type_view)
        required = infer_required(self, type_view)
        options = infer_options(
            self,
            types,
            help_formatter=help_formatter,
            propagated_arguments=propagated_arguments,
            state=state,
        )
        alias_map = build_alias_map(options)
        group = infer_group(self)

        return dataclasses.replace(
            self,
            field_name=field_name,
            types=types,
            required=required,
            options=options,
            alias_map=alias_map,
            group=group,
        )

    def resolve_name(self, name: str) -> str | None:
        """Return the canonical name for a typed-in name (canonical or alias).

        Returns `None` when `name` matches neither.
        """
        if name in self.options:
            return name
        if name in self.alias_map:
            return self.alias_map[name][0]
        return None

    def map_result(
        self,
        prog: str,
        parsed_args: dict[str, Any],
        *,
        output: Output,
        state: State[Any] | None = None,
        input: TextIO | None = None,
    ) -> tuple[Resolved[Any], dict[Any, Any]]:
        option_name = parsed_args.pop("__name__")
        typed_name = parsed_args.pop("__typed_name__", None)
        canonical = self.resolve_name(option_name) or option_name
        if typed_name is not None and typed_name != canonical:
            self._warn_deprecated_alias(output, typed_name)
        option = self.options[canonical]
        return option.map_result(
            option, prog, parsed_args, output=output, state=state, input=input
        )

    def _warn_deprecated_alias(self, output: Output, typed_name: str) -> None:
        _, alias = self.alias_map[typed_name]
        if not alias.deprecated:
            return

        message = f"Command alias `{typed_name}` is deprecated"
        if isinstance(alias.deprecated, str):
            message += f": {alias.deprecated}"
        output.error(message)

    def available_options(self) -> list[Command[Any]]:
        return [o for o in self.options.values() if not o.hidden]

    def names(self) -> list[str]:
        return [n for n, o in self.options.items() if not o.hidden]

    def visible_aliases_for(self, canonical: str) -> list[Alias]:
        """Visible (non-hidden) aliases for the given canonical subcommand name."""
        command = self.options.get(canonical)
        if command is None:
            return []
        return [a for a in command.resolved_aliases() if not a.hidden]

    def all_visible_names(self) -> list[str]:
        """Canonical names plus visible aliases, in declaration order."""
        result: list[str] = []
        for name in self.names():
            result.append(name)
            for alias in self.visible_aliases_for(name):
                result.append(alias.name)
        return result

    def names_str(self, delimiter: str = ", ") -> str:
        return f"{delimiter.join(self.names())}"

    def completion(self, partial: str):
        return [Completion(o) for o in self.all_visible_names() if partial in o]


def infer_types(arg: Subcommand, type_view: TypeView[Any]) -> Iterable[type]:
    if arg.types is not Empty:
        return arg.types

    if type_view.is_union:
        return tuple(t.annotation for t in type_view.inner_types if not t.is_none_type)

    return (type_view.annotation,)


def infer_required(arg: Subcommand, annotation: TypeView[Any]) -> bool:
    if arg.required is not None:
        return arg.required

    return not annotation.is_optional


def infer_options(
    arg: Subcommand,
    types: Iterable[type],
    help_formatter: HelpFormattable | None = None,
    propagated_arguments: list[Arg[Any]] | None = None,
    state: State[Any] | None = None,
) -> dict[str, Command[Any]]:
    from cappa.command import Command

    if arg.options:
        return {
            name: Command.collect(  # pyright: ignore
                type_command,
                propagated_arguments=propagated_arguments,
                state=state,
            )
            for name, type_command in arg.options.items()
        }

    options: dict[str, Command[Any]] = {}
    for type_ in types:
        type_command: Command[Any] = Command.get(type_, help_formatter=help_formatter)  # pyright: ignore
        type_name = type_command.real_name()
        options[type_name] = Command.collect(  # pyright: ignore
            type_command, propagated_arguments=propagated_arguments
        )

    return options


def build_alias_map(
    options: dict[str, Command[Any]],
) -> dict[str, tuple[str, Alias]]:
    """Build alias name -> (canonical, Alias) for a set of subcommand options.

    Raises `ValueError` on collisions: an alias matching another command's
    canonical name, an alias colliding with another alias, or an alias that
    duplicates its own canonical name.
    """
    alias_map: dict[str, tuple[str, Alias]] = {}
    for canonical, command in options.items():
        for alias in command.resolved_aliases():
            if alias.name == canonical:
                raise ValueError(
                    f"Subcommand '{canonical}' has an alias matching its own name."
                )
            if alias.name in options:
                raise ValueError(
                    f"Subcommand alias '{alias.name}' (for '{canonical}') "
                    f"collides with another subcommand's name."
                )
            if alias.name in alias_map:
                other_canonical, _ = alias_map[alias.name]
                raise ValueError(
                    f"Subcommand alias '{alias.name}' is declared on both "
                    f"'{other_canonical}' and '{canonical}'."
                )
            alias_map[alias.name] = (canonical, alias)
    return alias_map


def infer_group(arg: Subcommand) -> Group:
    name = None
    order = 3

    if isinstance(arg.group, Group):
        return arg.group

    if isinstance(arg.group, str):
        name = arg.group

    if isinstance(arg.group, tuple):
        order, name = arg.group

    assert name
    return Group(name=name, order=order)


Subcommands: TypeAlias = Annotated[T, Subcommand]
DEFAULT_SUBCOMMAND = Subcommand()
