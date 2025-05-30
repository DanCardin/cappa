from __future__ import annotations

import typing
from collections.abc import Iterable
from dataclasses import dataclass, replace
from itertools import groupby
from typing import Sequence, cast

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

HelpFormattable: TypeAlias = typing.Callable[
    ["Command[typing.Any]", str], typing.List[Displayable]
]
ArgGroup: TypeAlias = typing.Tuple[
    typing.Tuple[str, bool], typing.List[typing.Union[Arg, Subcommand]]
]
Dimension: TypeAlias = typing.Tuple[int, int, int, int]

TextComponent = typing.Union[Text, Markdown, str]
ArgFormat: TypeAlias = typing.Union[
    TextComponent,
    typing.Sequence[
        typing.Union[
            TextComponent, typing.Callable[[Arg], typing.Union[TextComponent, None]]
        ]
    ],
    typing.Callable[[Arg], typing.Union[TextComponent, None]],
]


def create_version_arg(version: str | Arg | None = None) -> Arg | None:
    if not version:
        return None

    if isinstance(version, str):
        version = Arg(
            value_name=version,
            short=["-v"],
            long=["--version"],
            help="Show the version and exit.",
            group=Group(1, "Help", section=2),
            action=ArgAction.version,
        )

    if version.value_name is Empty:
        raise ValueError(
            "Expected explicit version `Arg` to supply version number as its name, like `Arg('1.2.3', ...)`"
        )

    if version.long is True:
        version = replace(version, long="--version")

    return version.normalize(
        action=ArgAction.version, field_name="version", default=None
    )


def create_help_arg(help: bool | Arg | None = True) -> Arg | None:
    if not help:
        return None

    if isinstance(help, bool):
        help = Arg(
            short=["-h"],
            long=["--help"],
            help="Show this message and exit.",
            group=Group(0, "Help", section=2),
            action=ArgAction.help,
        )

    return help.normalize(action=ArgAction.help, field_name="help", default=None)


def create_completion_arg(completion: bool | Arg = True) -> Arg | None:
    if not completion:
        return None

    if isinstance(completion, bool):
        completion = Arg(
            long=["--completion"],
            choices=["generate", "complete"],
            group=Group(2, "Help", section=2),
            help="Use `--completion generate` to print shell-specific completion source.",
            action=ArgAction.completion,
        )

    return completion.normalize(
        field_name="completion",
        action=ArgAction.completion,
        default=None,
    )


@dataclass(frozen=True)
class HelpFormatter:
    left_padding: Dimension = (0, 0, 0, 2)
    arg_format: ArgFormat = (
        Markdown("{help}"),
        Markdown("{choices}"),
        Markdown("{default}", style="dim italic"),
    )
    default_format: str = "(Default: {default})"

    default: typing.ClassVar[Self]

    def __call__(self, command: Command, prog: str) -> list[Displayable]:
        arg_groups = generate_arg_groups(command)

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

    def with_arg_format(self, _format: ArgFormat, *formats: ArgFormat) -> Self:
        format = _format if isinstance(_format, tuple) else (_format,)
        arg_format = (*format, *formats)
        return replace(self, arg_format=arg_format)

    def with_default_format(self, format: str) -> Self:
        return replace(self, default_format=format)


HelpFormatter.default = HelpFormatter()


def add_long_args(
    console: Console, help_formatter: HelpFormatter, arg_groups: list[ArgGroup]
) -> list:
    table = Table(box=None, expand=False, padding=help_formatter.left_padding)
    table.add_column(justify="left", ratio=1)
    table.add_column(style="cappa.help", ratio=2)

    for (group_name, _), args in arg_groups:
        table.add_row(
            Text(group_name, style="cappa.group", justify="left"),
            Text(style="cappa.group"),
        )
        for arg in args:
            if isinstance(arg, Arg):
                table.add_row(
                    Padding(format_arg_name(arg, ", "), help_formatter.left_padding),
                    format_arg(console, help_formatter, arg),
                )
            else:
                for option in arg.available_options():
                    table.add_row(*format_subcommand(help_formatter, option))

        table.add_row()

    return [table]


def format_arg(
    console: Console, help_formatter: HelpFormatter, arg: Arg
) -> Displayable:
    arg_format = help_formatter.arg_format
    if not isinstance(arg_format, Iterable) or isinstance(arg_format, str):
        arg_format = (arg_format,)

    segments: list[TextComponent] = []
    for format_segment in arg_format:
        assert isinstance(arg.default, Default)
        assert isinstance(arg.show_default, DefaultFormatter)

        default = arg.show_default.format_default(
            arg.default, help_formatter.default_format
        )

        choices = ""
        if arg.choices:
            choices = "Valid options: " + ", ".join(arg.choices) + "."

        context = {
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
            # no_wrap=c.no_wrap,
            end=c.end,
            # tab_size=c.tab_size,
            # spans=c.spans,
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


def format_subcommand(help_formatter: HelpFormatter, command: Command):
    return (
        Padding(
            f"[cappa.subcommand]{command.real_name()}[/cappa.subcommand]",
            help_formatter.left_padding,
        ),
        command.help,
    )


def format_short_help(command: Command, prog: str) -> Displayable:
    arg_groups = generate_arg_groups(command)
    return add_short_args(prog, arg_groups)


def generate_arg_groups(command: Command, include_hidden=False) -> list[ArgGroup]:
    def by_group_key(arg: Arg | Subcommand):
        return assert_type(arg.group, Group).key

    def by_group(arg: Arg | Subcommand):
        group = assert_type(arg.group, Group)
        return (group.name, group.exclusive)

    sorted_args = sorted(command.all_arguments, key=by_group_key)
    return [
        (g, [a for a in args if include_hidden or not a.hidden])
        for g, args in groupby(sorted_args, key=by_group)
    ]


def add_short_args(prog: str, arg_groups: list[ArgGroup]) -> str:
    segments: list[str] = [f"Usage: {prog}"]
    for _, args in arg_groups:
        for arg in args:
            segments.append(format_arg_name(arg, ", ", n=1))

    return " ".join(segments)


def format_arg_name(arg: Arg | Subcommand, delimiter, *, n=0) -> str:
    if isinstance(arg, Arg):
        has_value = not ArgAction.is_non_value_consuming(arg.action)

        arg_names = arg.names_str(delimiter, n=n)
        if not arg.is_option:
            arg_names = arg_names.upper()

            if arg.num_args == -1:
                arg_names = f"{arg_names} ..."

        text = f"[cappa.arg]{arg_names}[/cappa.arg]"

        if arg.is_option and has_value:
            name = cast(str, arg.value_name).upper()
            if arg.num_args == -1:
                name = f"{name} ..."

            text = f"{text} [cappa.arg.name]{name}[/cappa.arg.name]"

        if not arg.required:
            return rf"\[{text}]"

        return text

    arg_names = arg.names_str(",")
    return f"{{[cappa.subcommand]{arg_names}[/cappa.subcommand]}}"


def format_subcommand_names(names: list[str]):
    return ", ".join(f"[cappa.subcommand]{a}[/cappa.subcommand]" for a in names)
