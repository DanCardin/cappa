from __future__ import annotations

from typing import ClassVar

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import ContentSwitcher, DataTable, Static, Tab, Tabs

import cappa
from cappa.ui.multiple_choice import NonFocusableVerticalScroll


class CommandMetadata(DataTable):
    def __init__(
        self,
        command: cappa.Command,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.show_header = False
        self.zebra_stripes = True
        self.cursor_type = "none"
        self.command_schema = command

    def on_mount(self) -> None:
        self.add_columns("Key", "Value")
        schema = self.command_schema
        subcommands = (
            list(schema.subcommand.options.keys()) if schema.subcommand else []
        )
        value_args = schema.value_arguments(exclude_subcommand=True)
        positionals = [a for a in value_args if not a.short and not a.long]
        options = [a for a in value_args if a.short or a.long]
        self.add_rows(
            [
                (Text("Name", style="b"), schema.real_name()),
                (
                    Text("Subcommands", style="b"),
                    str(subcommands) if subcommands else "none",
                ),
                (Text("Arguments", style="b"), str(len(positionals))),
                (Text("Options", style="b"), str(len(options))),
            ]
        )


class CommandInfo(ModalScreen):
    COMPONENT_CLASSES: ClassVar[set[str]] = {"title", "subtitle"}

    BINDINGS: ClassVar = [Binding("q,escape", "close_modal", "Close Modal")]

    def __init__(
        self,
        command: cappa.Command,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(
            name=name,
            id=id,
            classes=classes,
        )
        self.command_schema = command

    def compose(self) -> ComposeResult:
        schema = self.command_schema
        title_style = self.get_component_rich_style("title")
        subtitle_style = self.get_component_rich_style("subtitle")
        modal_header = Text.assemble(
            (schema.real_name(), title_style), "\n", ("command info", subtitle_style)
        )
        with NonFocusableVerticalScroll(classes="command-info-container"):
            with Vertical(classes="command-info-header"):
                yield Static(modal_header, classes="command-info-header-text")
                tabs = Tabs(
                    Tab("Description", id="command-info-text"),
                    Tab("Metadata", id="command-info-metadata"),
                    classes="command-info-tabs",
                )
                tabs.focus()
                yield tabs

            command_info = (
                schema.help.strip() if schema.help else "No description available"
            )

            with ContentSwitcher(
                initial="command-info-text", id="command-info-switcher"
            ):
                yield Static(
                    command_info, id="command-info-text", classes="command-info-text"
                )
                yield CommandMetadata(
                    command=self.command_schema,
                    id="command-info-metadata",
                    classes="command-info-metadata",
                )

    @on(Tabs.TabActivated)
    def switch_content(self, event: Tabs.TabActivated) -> None:
        self.query_one(ContentSwitcher).current = event.tab.id

    def action_close_modal(self):
        self.app.pop_screen()
