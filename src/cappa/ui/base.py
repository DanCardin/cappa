from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Tuple, TypeVar, Union
from webbrowser import open as open_url

from rich.highlighter import ReprHighlighter
from rich.style import StyleType
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Static,
    Tree,
)
from textual.widgets.tree import TreeNode

import cappa
from cappa.ui.about import AboutDialog
from cappa.ui.command_info import CommandInfo
from cappa.ui.command_tree import CommandTree
from cappa.ui.data import CommandData
from cappa.ui.form import CommandForm
from cappa.ui.multiple_choice import NonFocusableVerticalScroll

Textable = Union[str, "Text", Tuple[str, StyleType]]

T = TypeVar("T")


def run(cls):
    app = CLIApp(cls)
    app.run()


def make_app(cls) -> CLIApp:
    """Return a CLIApp instance. Use with `textual serve module:app --dev`."""
    return CLIApp(cls)


def _resolve_target(cls) -> str:
    """Resolve 'module:ClassName' even when cls is defined in __main__."""
    import inspect
    import sys

    if cls.__module__ != "__main__":
        return f"{cls.__module__}:{cls.__qualname__}"

    try:
        file = Path(inspect.getfile(cls)).resolve()
    except (TypeError, OSError) as e:
        raise ValueError(f"Cannot locate source file for {cls.__qualname__}") from e

    for entry in sys.path:
        base = Path(entry).resolve() if entry else Path.cwd()
        try:
            rel = file.relative_to(base)
            parts = rel.with_suffix("").parts
            if parts:
                return f"{'.'.join(parts)}:{cls.__qualname__}"
        except ValueError:
            continue

    raise ValueError(
        f"Cannot determine importable module for {cls.__qualname__}. "
        "Run via a named module (python -m mymodule) or import from a package."
    )


def serve(cls, host: str = "localhost", port: int = 8000):
    """Serve the CLI as a web TUI via textual-serve."""
    import sys

    from textual_serve.server import Server

    target = _resolve_target(cls)
    command = f"{sys.executable} -m cappa.ui.tui {target}"
    Server(command, host=host, port=port).serve()


class CLIApp(App):
    CSS_PATH = Path(__file__).parent / "web.scss"

    def __init__(self, cls) -> None:
        super().__init__()

        self.command = cappa.collect(cls)

    def on_mount(self):
        self.push_screen(CommandBuilder(self.command))

    @on(Button.Pressed, "#home-exec-button")
    def on_button_pressed(self):
        self.exit()

    def action_focus_command_tree(self) -> None:
        try:
            command_tree = self.query_one(CommandTree)
        except NoMatches:
            return

        command_tree.focus()

    def action_show_command_info(self) -> None:
        command_builder = self.query_one(CommandBuilder)
        if command_builder.selected_command is None:
            return
        self.push_screen(CommandInfo(command_builder.selected_command))

    def action_visit(self, url: str) -> None:
        open_url(url)


class CommandBuilder(Screen):
    COMPONENT_CLASSES: ClassVar = {"version-string", "prompt", "command-name-syntax"}

    BINDINGS: ClassVar = [
        Binding(key="ctrl+r", action="close_and_run", description="Exit & Run"),
        Binding(
            key="ctrl+t", action="focus_command_tree", description="Focus Command Tree"
        ),
        Binding(key="ctrl+o", action="show_command_info", description="Command Info"),
        Binding(key="?", action="about", description="About"),
    ]

    def __init__(self, command: cappa.Command):
        super().__init__()
        self.command = command

        self.selected_command: cappa.Command | None = None
        self._selected_node: TreeNode[cappa.Command] | None = None
        self.command_data: CommandData | None = None
        self.highlighter = ReprHighlighter()

    def compose(self) -> ComposeResult:
        title_parts: list[Textable] = [Text(self.command.real_name(), style="b")]

        version = self.command.version()
        if version:
            version_style = self.get_component_rich_style("version-string")
            title_parts.extend(["\n", (f"v{version}", version_style)])

        title = Text.assemble(*title_parts)

        with Header(id="header"):
            yield Static(title, id="home-command-description")

        with Vertical():
            with Horizontal(id="home-body"):
                subcommand = self.command.subcommand
                sidebar_id = "home-sidebar" if subcommand else "no-sidebar"

                with Vertical(id=sidebar_id):
                    tree = CommandTree("Commands", self.command)
                    yield tree

                    if subcommand:
                        tree.focus()

                yield NonFocusableVerticalScroll(Static(""), id="home-body-scroll")

            with Horizontal(id="home-exec-preview"):
                with NonFocusableVerticalScroll():
                    yield Static("", id="home-exec-preview-static")

                yield Button.success("Close & Run", id="home-exec-button")

        yield Footer()

    def _build_argv(self) -> list[str]:
        """Build argv for cappa.invoke: subcommand path + arg values."""
        path: list[str] = []
        node = self._selected_node
        if node is not None:
            current = node
            while current.parent is not None:
                cmd = current.data
                if cmd is not None and cmd is not self.command:
                    path.append(cmd.real_name())
                current = current.parent
            path.reverse()
        arg_values: list[str] = (
            self.command_data.to_cli_args(include_root_command=False)
            if self.command_data
            else []
        )
        return path + arg_values

    def action_close_and_run(self) -> None:
        if self.command_data is None:
            return

        try:
            cappa.invoke(self.command, argv=self._build_argv())
        except Exception as e:
            self.app.exit(e, message=str(e), return_code=1)
        else:
            self.app.exit()

    def action_about(self) -> None:
        self.app.push_screen(AboutDialog(self.command))

    async def _refresh_command_form(self, node: TreeNode[cappa.Command]):
        command = node.data
        assert command

        self.selected_command = command
        self._selected_node = node

        description_box = self.query_one("#home-command-description", Static)
        description_text = command.help or ""
        description_text = f"[b]{node.label if command.subcommand else command.real_name()}[/]\n{description_text}"
        description_box.update(description_text)

        self._update_execution_string_preview(command, self.command_data)

        parent = self.query_one("#home-body-scroll", VerticalScroll)
        for child in parent.children:
            await child.remove()

        # Process the metadata for this command and mount corresponding widgets

        command_form = CommandForm(command=command)
        await parent.mount(command_form)
        if not self.command.subcommand:
            command_form.focus()

    @on(Tree.NodeHighlighted)
    async def on_node_highlighted(
        self, event: Tree.NodeHighlighted[cappa.Command]
    ) -> None:
        if event.node:
            await self._refresh_command_form(event.node)

    @on(Tree.NodeSelected)
    async def on_node_selected(self, event: Tree.NodeSelected[cappa.Command]) -> None:
        if event.node:
            await self._refresh_command_form(event.node)

    @on(CommandForm.Changed)
    def update_command_data(self, event: CommandForm.Changed) -> None:
        self.command_data = event.command_data
        self._update_execution_string_preview(self.selected_command, self.command_data)

    def _update_execution_string_preview(
        self, command: cappa.Command[T] | None, command_data: T
    ) -> None:
        if self.command_data is None:
            return

        command_name_syntax_style = self.get_component_rich_style("command-name-syntax")
        argv = self._build_argv()
        argv_text = Text(" ").join(Text(a) for a in argv)
        root_prefix = Text(f"{self.command.real_name()} ", command_name_syntax_style)
        highlighted_new_value = Text.assemble(root_prefix, self.highlighter(argv_text))
        prompt_style = self.get_component_rich_style("prompt")
        preview_string = Text.assemble(("$ ", prompt_style), highlighted_new_value)
        self.query_one("#home-exec-preview-static", Static).update(preview_string)
