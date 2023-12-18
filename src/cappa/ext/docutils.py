from __future__ import annotations

import importlib
import importlib.util
import io
import logging
from typing import Any, ClassVar

from rich.console import Console

import cappa
from cappa.help import format_help, generate_arg_groups
from cappa.output import Displayable, theme
from cappa.typing import missing

try:
    importlib.util.find_spec("docutils")
except ImportError:  # pragma: no cover
    raise ImportError(
        "The ext.docutils package can only be used if 'docutils' is installed."
    )

from docutils import nodes
from docutils.parsers.rst import Directive, directives

log = logging.getLogger(__name__)

FONT_FAMILY = (
    """font-family:Menlo,"DejaVu Sans Mono",consolas,"Courier New",monospace"""
)


def setup(app) -> None:  # pragma: no cover
    app.add_directive("cappa", CappaDirective)


class CappaDirective(Directive):
    has_content = False
    required_arguments = 1
    option_spec: ClassVar[dict[str, Any]] = {
        "style": directives.unchanged,
        "terminal-width": directives.unchanged,
    }

    def run(self) -> list[nodes.Node]:
        path = self.arguments[0]
        style = self.options.get("style", "terminal")
        terminal_width = int(self.options.get("terminal-width", "0"))

        module_path, item_name = path.rsplit(".", 1)

        module = importlib.import_module(module_path)
        item = getattr(module, item_name)

        command = cappa.collect(item)
        if style == "terminal":
            return render_to_terminal(command, terminal_width)

        if style == "native":
            return render_to_docutils(command, self.state.document)

        raise ValueError(f"Unrecognized style {style}")


def render_to_terminal(command: cappa.Command, terminal_width: int):
    raw_help: list[Displayable] = format_help(command, command.real_name())

    line_wrap = ""
    if terminal_width == 0:
        line_wrap = "white-space: pre-wrap;"
        terminal_width = 99999

    console = Console(
        record=True,
        theme=theme,
        file=io.StringIO(),
        soft_wrap=True,
        width=terminal_width,
    )
    console.print(*raw_help)

    style = " ".join([line_wrap, FONT_FAMILY])

    code_format = f'<pre style="{style}"><code>{{code}}</code></pre>'
    html = console.export_html(inline_styles=True, code_format=code_format)
    return [nodes.raw(text=html, format="html")]


def render_to_docutils(command: cappa.Command, document):
    section = nodes.section()
    document.note_implicit_target(section)

    section += nodes.title(text=command.real_name())

    command_content = nodes.paragraph()
    section += command_content

    description = []
    if command.help:
        description.append(command.help)
    if command.description:
        description.append(command.description)

    section += nodes.paragraph(text="\n\n".join(description))

    for group_name, group in sorted(generate_arg_groups(command)):
        command_options = [arg for arg in group if isinstance(arg, cappa.Arg)]
        if command_options:
            section += nodes.subtitle(text=group_name)

            option = nodes.bullet_list()
            section += option

            for arg in command_options:
                option_content = nodes.list_item()
                option += option_content

                names = arg.names()
                if names:
                    for name in names:
                        option_content += nodes.literal(text=name)
                else:
                    name = arg.field_name
                    name += f" {arg.value_name.upper()}"
                    option_content += nodes.literal(text=name)

                if arg.default is not missing and arg.default is not None:
                    default = str(arg.default)

                    option_content += nodes.inline(text=" (")
                    option_content += nodes.literal(text=default)
                    option_content += nodes.inline(text=")")

                if arg.help:
                    option_content += nodes.inline(text=f": {arg.help}")

        command_subcommands = [
            arg for arg in group if isinstance(arg, cappa.Subcommand)
        ]
        if command_subcommands:
            for subcmd in command_subcommands:
                for option in subcmd.options.values():
                    section += render_to_docutils(option, document)

    return [section]
