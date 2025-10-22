from __future__ import annotations

import typing
from collections.abc import Iterable
from dataclasses import dataclass, replace
from itertools import groupby
from typing import Any, List, Sequence, Tuple, cast

from rich.console import Console, NewLine
from rich.markdown import Markdown
from rich.padding import Padding
from rich.table import Table
from rich.text import Text
from typing_extensions import Self, TypeAlias

from cappa.arg import Arg, ArgAction, Group
from cappa.default import Default, DefaultFormatter
from cappa.output import Displayable
from cappa.subcommand import Subcommand
from cappa.type_view import Empty
from cappa.typing import assert_type

if typing.TYPE_CHECKING:
    from cappa.command import Command

Dimension: TypeAlias = typing.Tuple[int, int, int, int]


@dataclass(frozen=True)
class FieldGroup:
    """A group of arguments or a subcommand sharing the same field_name.

    Either `args` or `subcommand` will be set, never both.
    """

    field_name: str | None
    required: bool
    args: list[Arg[Any]] | None = None
    subcommand: Subcommand | None = None


@dataclass(frozen=True)
class ArgGroup:
    """A group of arguments/subcommands organized by their Group."""

    name: str
    field_groups: list[FieldGroup]

    @staticmethod
    def _by_group_key(arg: Arg[Any] | Subcommand) -> tuple[int, int, str, bool]:
        return assert_type(arg.group, Group).key

    @staticmethod
    def _by_group(arg: Arg[Any] | Subcommand) -> str:
        return assert_type(arg.group, Group).name

    @classmethod
    def collect(
        cls, command: Command[Any], include_hidden: bool = False
    ) -> list[ArgGroup]:
        """Collect and group arguments from a command by their Group."""
        sorted_args = sorted(command.all_arguments, key=cls._by_group_key)

        result: list[ArgGroup] = []
        for name, args in groupby(sorted_args, key=cls._by_group):
            items = [a for a in args if include_hidden or not a.hidden]

            field_grouped: dict[str | None, list[Arg[Any] | Subcommand]] = {}
            for item in items:
                field_name = item.field_name if item.field_name is not Empty else None
                if field_name not in field_grouped:
                    field_grouped[field_name] = []
                field_grouped[field_name].append(item)

            field_groups: list[FieldGroup] = []
            for field_name, items in field_grouped.items():
                # Validate that items are all Args or all Subcommands
                first_item = items[0]
                if isinstance(first_item, Arg):
                    # Validate all are Args
                    if not all(isinstance(item, Arg) for item in items):
                        raise ValueError(  # pragma: no cover
                            f"FieldGroup with field_name={field_name!r} contains mixed types: "
                            f"Args and Subcommands cannot share the same field_name"
                        )
                    group_args = cast(List[Arg[Any]], items)

                    # All items must have the same requiredness
                    required_values = {arg.required for arg in group_args}
                    assert len(required_values) == 1, (
                        f"All items with field_name={field_name!r} must have the same "
                        f"required value, got: {required_values}"
                    )
                    required = cast(bool, required_values.pop())
                    field_groups.append(
                        FieldGroup(field_name, required, args=group_args)
                    )
                else:
                    assert len(items) == 1
                    field_groups.append(
                        FieldGroup(
                            field_name,
                            cast(bool, first_item.required),
                            subcommand=first_item,
                        )
                    )

            result.append(cls(name=name, field_groups=field_groups))

        return result


TextComponent = typing.Union[Text, Markdown, str]
ArgFormat: TypeAlias = typing.Union[
    TextComponent,
    typing.Callable[[Arg[Any]], typing.Union[TextComponent, None]],
]
ArgFormats: TypeAlias = typing.Sequence[ArgFormat]


class HelpFormattable(typing.Protocol):
    left_padding: Dimension
    arg_format: ArgFormat | ArgFormats
    default_format: str

    def long(
        self, command: Command[Any], prog: str
    ) -> list[Displayable]: ...  # pragma: no cover

    def short(
        self, command: Command[Any], prog: str
    ) -> Displayable: ...  # pragma: no cover


@dataclass(frozen=True)
class HelpFormatter(HelpFormattable):
    left_padding: Dimension = (0, 0, 0, 2)
    arg_format: ArgFormat | ArgFormats = (
        Markdown("{help}"),
        Markdown("{choices}"),
        Markdown("{default}", style="dim italic"),
    )
    default_format: str = "(Default: {default})"

    default: typing.ClassVar[HelpFormatter]

    def long(self, command: Command[Any], prog: str) -> list[Displayable]:
        arg_groups = ArgGroup.collect(command)

        lines: list[Displayable] = []
        lines.append(add_short_args(prog, arg_groups))

        if command.help:
            lines.append(NewLine())
            lines.append(Padding(Markdown(f"**{command.help}**"), self.left_padding))
        if command.description:
            lines.append(NewLine())
            lines.append(Padding(Markdown(command.description), self.left_padding))

        console = Console()
        lines.extend(add_long_args(console, self, arg_groups))
        return lines

    def short(self, command: Command[Any], prog: str) -> Displayable:
        arg_groups = ArgGroup.collect(command)
        return add_short_args(prog, arg_groups)

    def with_arg_format(
        self, _format: ArgFormat | tuple[ArgFormat, ...], *formats: ArgFormat
    ) -> Self:
        format = cast(
            Tuple[ArgFormat, ...], _format if isinstance(_format, tuple) else (_format,)
        )
        arg_format = (*format, *formats)
        return replace(self, arg_format=arg_format)

    def with_default_format(self, format: str) -> Self:
        return replace(self, default_format=format)


HelpFormatter.default = HelpFormatter()


def add_long_args(
    console: Console, help_formatter: HelpFormatter, arg_groups: list[ArgGroup]
) -> list[Table]:
    table = Table(box=None, expand=False, padding=help_formatter.left_padding)
    table.add_column(justify="left", ratio=1)
    table.add_column(style="cappa.help", ratio=2)

    for group in arg_groups:
        table.add_row(
            Text(group.name, style="cappa.group", justify="left"),
            Text(style="cappa.group"),
        )

        for field_group in group.field_groups:
            if field_group.args:
                combined = format_arg_name(field_group, ", ")

                help_text = format_args(console, help_formatter, *field_group.args)

                table.add_row(
                    Padding(combined, help_formatter.left_padding),
                    help_text,
                )

            else:
                assert field_group.subcommand
                for option in field_group.subcommand.available_options():
                    table.add_row(*format_subcommand(help_formatter, option))

        table.add_row()

    return [table]


def format_args(
    console: Console, help_formatter: HelpFormattable, *args: Arg[Any]
) -> Displayable:
    """Format multiple args with the same field_name by concatenating their help texts."""
    segments: list[TextComponent] = []

    for arg in args:
        assert isinstance(arg.default, Default)
        assert isinstance(arg.show_default, DefaultFormatter)

        unknown_arg_format = help_formatter.arg_format
        if isinstance(unknown_arg_format, Iterable) and not isinstance(
            unknown_arg_format, str
        ):
            arg_format = cast(Sequence[ArgFormat], unknown_arg_format)
        else:
            arg_format = (unknown_arg_format,)

        for format_segment in arg_format:
            default = arg.show_default.format_default(
                arg.default, help_formatter.default_format
            )

            choices = ""
            if arg.choices:
                choices = "Valid options: " + ", ".join(arg.choices) + "."

            context: dict[str, Any] = {
                "help": arg.help or "",
                "default": default,
                "choices": choices,
                "arg": arg,
            }

            if callable(format_segment):
                format_segment = cast(TextComponent, format_segment(arg))

            format_segment_text = _get_text_component_text(format_segment)
            if not format_segment_text:
                continue

            formatted_text = format_segment_text.format(**context)
            segment = _replace_rich_text_component(format_segment, formatted_text)

            if segment:
                segments.append(segment)

    return _markdown_to_text(console, segments)


def _markdown_to_text(console: Console, renderables: Sequence[TextComponent]) -> Text:
    result = Text()
    for renderable in renderables:
        if isinstance(renderable, Markdown):
            for segment in console.render(renderable):
                text = segment.text.strip("\n")
                if text.startswith(" "):  # dedup leading spaces
                    text = " " + text.lstrip()
                if text.endswith(" "):  # dedup trailing spaces
                    text = text.rstrip() + " "
                if text:
                    result.append(Text(text, style=segment.style or "", end=""))
        else:
            if result:
                result.append(" ")

            if isinstance(renderable, str):
                renderable = Text.from_markup(renderable)

            result.append(renderable)

    return result


def _get_text_component_text(c: TextComponent) -> str:
    if isinstance(c, Text):
        return c.plain

    if isinstance(c, Markdown):
        return c.markup

    return c


def _replace_rich_text_component(c: TextComponent, text: str) -> TextComponent:
    if isinstance(c, Text):
        return Text.from_markup(
            text,
            style=c.style,
            justify=c.justify,
            overflow=c.overflow,
            end=c.end,
        )

    if isinstance(c, Markdown):
        return Markdown(
            text,
            code_theme=c.code_theme,
            justify=c.justify,
            style=c.style,
            hyperlinks=c.hyperlinks,
            inline_code_lexer=c.inline_code_lexer,
            inline_code_theme=c.inline_code_theme,
        )

    return text


def format_subcommand(help_formatter: HelpFormatter, command: Command[Any]):
    return (
        Padding(
            f"[cappa.subcommand]{command.real_name()}[/cappa.subcommand]",
            help_formatter.left_padding,
        ),
        command.help,
    )


def add_short_args(prog: str, arg_groups: list[ArgGroup]) -> str:
    segments: list[str] = [f"Usage: {prog}"]
    for group in arg_groups:
        for field_group in group.field_groups:
            segments.append(format_arg_name(field_group, ", ", n=1))

    return " ".join(segments)


def format_arg_name(item: FieldGroup, delimiter: str, *, n: int = 0) -> str:
    """Format the name(s) of args/subcommands for display.

    If given a FieldGroup, formats all items together with appropriate brackets.
    If given a single Arg/Subcommand, formats just that item.
    """
    if item.args:
        parts: list[str] = []
        for arg in item.args:
            has_value = (
                not ArgAction.is_non_value_consuming(arg.action) and arg.num_args != 0
            )

            arg_names = arg.names_str(delimiter, n=n)
            if not arg.is_option:
                arg_names = arg_names.upper()

                if arg.num_args == -1:
                    arg_names = f"{arg_names} ..."

            text = f"[cappa.arg]{arg_names}[/cappa.arg]"

            # if arg.is_option and arg.num_args != 0:
            if arg.is_option and has_value:
                name = cast(str, arg.value_name).upper()
                if arg.num_args == -1:
                    name = f"{name} ..."

                text = f"{text} [cappa.arg.name]{name}[/cappa.arg.name]"

            parts.append(text)
        combined = ", ".join(parts)

        if not item.required:
            return f"[{combined}]"
        return combined

    assert item.subcommand is not None
    arg_names = item.subcommand.names_str(",")
    return f"{{[cappa.subcommand]{arg_names}[/cappa.subcommand]}}"


def format_subcommand_names(names: list[str]):
    return ", ".join(f"[cappa.subcommand]{a}[/cappa.subcommand]" for a in names)
