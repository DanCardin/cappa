from __future__ import annotations

import functools
import typing
from typing import Any, Iterable, Union

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.css.query import NoMatches
from textual.widget import Widget
from textual.widgets import (
    Button,
    Checkbox,
    Input,
    Label,
    Select,
    Static,
)
from type_lens.type_view import TypeView
from typing_extensions import TypeAlias

from cappa import Arg
from cappa.arg import ArgAction
from cappa.typing import assert_type
from cappa.ui.multiple_choice import MultipleChoice

ControlWidgetType: TypeAlias = Union[Input, Checkbox, MultipleChoice, Select]


class ControlGroup(Vertical):
    pass


class ControlGroupsContainer(Vertical):
    pass


@functools.total_ordering
class ValueNotSupplied:
    def __eq__(self, other):
        return isinstance(other, ValueNotSupplied)

    def __lt__(self, other):
        return False

    def __bool__(self):
        return False


class ParameterControls(Widget):
    def __init__(
        self,
        arg: Arg,
        name: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            name=name,
            id=assert_type(arg.field_name, str),
            classes=classes,
            disabled=disabled,
        )
        self.arg = arg
        self.first_control: Widget | None = None

    def apply_filter(self, filter_query: str) -> bool:
        """Show or hide this ParameterControls depending on whether it matches the filter query or not.

        Args:
            filter_query: The string to filter on.

        Returns:
            True if the filter matched (and the widget is visible).
        """
        help_text = getattr(self.arg, "help", "") or ""
        if not filter_query:
            should_be_visible = True
            self.display = should_be_visible
        else:
            names = self.arg.names()
            name_contains_query = any(filter_query in n.casefold() for n in names)
            help_contains_query = filter_query in help_text.casefold()
            should_be_visible = name_contains_query or help_contains_query
            self.display = should_be_visible

        # Update the highlighting of the help text
        if help_text:
            try:
                help_label = self.query_one(".command-form-control-help-text", Static)
                new_help_text = Text(help_text)
                new_help_text.highlight_words(
                    filter_query.split(), "black on yellow", case_sensitive=False
                )
                help_label.update(new_help_text)
            except NoMatches:
                pass

        return bool(self.display)

    def compose(self) -> ComposeResult:
        label = self._make_command_form_control_label(self.arg)

        # If there are N defaults, we render the "group" N times.
        # Each group will contain `nargs` widgets.
        with ControlGroupsContainer():
            if self.arg.action not in {ArgAction.store_true, ArgAction.store_false}:
                yield Label(label, classes="command-form-label")

            for control in self.make_control(self.arg):
                if self.first_control is None:
                    self.first_control = control

                yield control

        # If it's a multiple, and it's a Choice parameter, then we display
        # our special case MultiChoice widget, and so there's no need for this
        # button.
        if self.arg.multiple or (self.arg.num_args == -1 and self.arg.choices):
            with Horizontal(classes="add-another-button-container"):
                yield Button("+ value", variant="success", classes="add-another-button")

        # Render the dim help text below the form controls
        if self.arg.help:
            yield Static(self.arg.help, classes="command-form-control-help-text")

    def make_widget_group(self) -> Iterable[Widget]:
        """Yield a fresh set of widgets for one value entry."""
        yield from self.make_control(self.arg)

    @on(Button.Pressed, ".add-another-button")
    def add_another_widget_group(self, event: Button.Pressed) -> None:
        widget_group = list(self.make_widget_group())
        widget_group[0].focus()
        control_group = ControlGroup(*widget_group)
        if len(widget_group) <= 1:
            control_group.add_class("single-item")
        control_groups_container = self.query_one(ControlGroupsContainer)
        control_groups_container.mount(control_group)
        event.button.scroll_visible(animate=False)

    @staticmethod
    def _get_form_control_value(control: ControlWidgetType) -> Any:
        if isinstance(control, MultipleChoice):
            return control.selected

        if isinstance(control, Select):
            if control.value is Select.BLANK:
                return ValueNotSupplied()

        if isinstance(control, Input):
            if control.value == "":
                return ValueNotSupplied()

        # TODO: We should only return "" when user selects a checkbox - needs custom widget.
        if isinstance(control, Checkbox):
            return control.value

        return control.value

    def get_values(self) -> list[Any]:
        controls = list(self.query(f".{self.arg.field_name}"))
        return [
            self._get_form_control_value(typing.cast(ControlWidgetType, control))
            for control in controls
        ]

    def make_control(self, arg: Arg):
        control: ControlWidgetType
        if arg.action in {ArgAction.store_true, ArgAction.store_false}:
            control = Checkbox(
                typing.cast(str, arg.value_name),
                button_first=True,
                classes=f"command-form-checkbox {arg.field_name}",
                value=bool(arg.default or False),
            )

        elif arg.choices:
            if arg.multiple:
                mc_defaults = (
                    [(v,) for v in arg.default]
                    if isinstance(arg.default, list)
                    else None
                )
                control = MultipleChoice(
                    [Text(c) for c in arg.choices],
                    classes=f"command-form-multiple-choice {arg.field_name}",
                    defaults=mc_defaults,
                )
            else:
                default = arg.default if arg.default in arg.choices else Select.BLANK
                control = Select(
                    [(choice, choice) for choice in arg.choices],
                    value=default,
                    classes=f"{arg.field_name} command-form-select",
                )

        else:
            control = Input(
                classes=f"command-form-input {arg.field_name}",
            )

        yield control

    @staticmethod
    def _make_command_form_control_label(arg: Arg) -> Text:
        type_view = assert_type(arg.type_view, TypeView)
        annotation = type_view.repr_type

        if arg.short or arg.long:
            name_text = Text(" / ", style="dim").join(Text(n) for n in arg.names())
        else:
            name_text = Text(typing.cast(str, arg.field_name))

        suffix = (
            f"[dim]{' multiple' if arg.multiple else ''} {annotation}[/]"
            f"{' [b red]*[/]required' if arg.required else ''}"
        )
        return Text.assemble(name_text, Text.from_markup(suffix))

    def focus(self, scroll_visible: bool = True):
        if self.first_control is not None:
            self.first_control.focus(scroll_visible)
        return self
