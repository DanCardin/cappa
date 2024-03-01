from __future__ import annotations

import dataclasses

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Label

from cappa import Arg, Command
from cappa.subcommand import Subcommand
from cappa.ui.data import ArgData, CommandData
from cappa.ui.multiple_choice import NonFocusableVerticalScroll
from cappa.ui.parameter_controls import ParameterControls


@dataclasses.dataclass
class FormControlMeta:
    widget: Widget
    meta: Arg


class CommandForm(Widget):
    DEFAULT_CSS = """    
    .command-form-heading {
        padding: 1 0 0 1;
        text-style: u;
        color: $text;
    }
    .command-form-input {        
        border: tall transparent;
    }
    .command-form-label {
        padding: 1 0 0 1;
    }
    .command-form-checkbox {
        background: $boost;
        margin: 1 0 0 0;
        padding-left: 1;
        border: tall transparent;
    }
    .command-form-checkbox:focus {
      border: tall $accent;      
    }
    .command-form-checkbox:focus > .toggle--label {
        text-style: none;
    }
    .command-form-command-group {
        
        margin: 1 2;
        padding: 0 1;
        height: auto;
        background: $foreground 3%;
        border: panel $background;
        border-title-color: $text 80%;
        border-title-style: bold;
        border-subtitle-color: $text 30%;
        padding-bottom: 1;
    }
    .command-form-command-group:focus-within {
        border: panel $primary;
    }
    .command-form-control-help-text {        
        height: auto;
        color: $text 40%;
        padding-top: 0;
        padding-left: 1;
    }
    """

    class Changed(Message):
        def __init__(self, command_data: CommandData):
            super().__init__()
            self.command_data = command_data

    def __init__(
        self,
        command: Command,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.command = command
        self.first_control: ParameterControls | None = None

    def compose(self) -> ComposeResult:
        path_from_root = iter(reversed([self.command]))  # self.command.path_from_root))
        command_node = next(path_from_root)
        with NonFocusableVerticalScroll():
            yield Input(
                placeholder="Search...",
                classes="command-form-filter-input",
                id="search",
            )

            while command_node is not None:
                arguments = command_node.value_arguments()
                if arguments:
                    command_name = command_node.real_name()
                    with VerticalScroll(
                        classes="command-form-command-group", id=command_name
                    ) as v:
                        is_inherited = command_node is not self.command
                        v.border_title = f"{'↪ ' if is_inherited else ''}{command_name}"
                        if is_inherited:
                            v.border_title += " [dim not bold](inherited)"

                        yield Label("Arguments", classes="command-form-heading")
                        for arg in arguments:
                            if isinstance(arg, Subcommand):
                                continue

                            control = ParameterControls(arg)
                            if self.first_control is None:
                                self.first_control = control
                            yield control

                command_node = next(path_from_root, None)

    def on_mount(self) -> None:
        self._form_changed()

    def on_input_changed(self) -> None:
        self._form_changed()

    def on_select_changed(self) -> None:
        self._form_changed()

    def on_checkbox_changed(self) -> None:
        self._form_changed()

    def on_multiple_choice_changed(self) -> None:
        self._form_changed()

    def _form_changed(self) -> None:
        arg_data = []

        # For each of the options in the schema for this command,
        # lets grab the values the user has supplied for them in the form.
        for arg in self.command.value_arguments(exclude_subcommand=True):
            parameter_control = self.query_one(
                f"#{arg.field_name}", ParameterControls
            )
            values = parameter_control.get_values()
            option_data = ArgData(arg, values)
            arg_data.append(option_data)

        command_data = CommandData(
            command=self.command,
            args_data=arg_data,
            parent=None,
        )

        # XXX: Doesnt handle subcommands, but should
        self.post_message(self.Changed(command_data))

    def focus(self, scroll_visible: bool = True):
        assert self.first_control
        self.first_control.focus(scroll_visible)
        return self

    @on(Input.Changed, ".command-form-filter-input")
    def apply_filter(self, event: Input.Changed) -> None:
        filter_query = event.value
        all_controls = self.query(ParameterControls)
        for control in all_controls:
            filter_query = filter_query.casefold()
            control.apply_filter(filter_query)
