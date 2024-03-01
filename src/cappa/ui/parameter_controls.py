from __future__ import annotations

import functools
from functools import partial
from typing import Any, Iterable, TypeAlias, Union, cast

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

    def __bool__(self: Arg):
        is_text_type = argument_type in text_click_types or isinstance(
            argument_type, text_types
        )
        if is_text_type:
            return self.make_text_control
        elif argument_type == click.BOOL:
            return self.make_checkbox_control
        elif isinstance(argument_type, click.types.Choice):
            return partial(self.make_choice_control, choices=argument_type.choices)
        else:
            return self.make_text_control


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
            name = self.arg.name
            if isinstance(name, str):
                # Argument names are strings, there's only one name
                name_contains_query = filter_query in name.casefold()
                should_be_visible = name_contains_query
            else:
                # Option names are lists since they can have multiple names (e.g. -v and --verbose)
                name_contains_query = any(
                    filter_query in name.casefold() for name in self.arg.name
                )
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

        return should_be_visible

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
        """For this option, yield a single set of widgets required to receive user input for it."""
        arg: Arg = self.arg
        control = self.make_control(arg)

        if isinstance(control, Input):
            control.value = str(arg.default)
            control.placeholder = f"{arg.default} (default)"
        elif isinstance(control, Select):
            control.value = str(arg.default)
            control.prompt = f"{arg.default} (default)"
        yield from control

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
    def _get_form_control_value(control: Widget) -> Any:
        if isinstance(control, MultipleChoice):
            return control.selected

        if isinstance(control, Select):
            if control.value is None:
                return ValueNotSupplied()

        if isinstance(control, Input):
            if control.value == "":
                return ValueNotSupplied()

        # TODO: We should only return "" when user selects a checkbox - needs custom widget.
        if isinstance(control, Checkbox):
            return control.value

        return control.value

    def get_values(self) -> ...:
        controls = list(self.query(f".{self.arg.field_name}"))
        return [self._get_form_control_value(control) for control in controls]

        def list_to_tuples(
            lst: list[int | float | str], tuple_size: int
        ) -> list[tuple[int | float | str, ...]]:
            if tuple_size == 0:
                return [tuple()]
            elif tuple_size == -1:
                # Unspecified number of arguments as per Click docs.
                tuple_size = 1
            return [
                tuple(lst[i : i + tuple_size]) for i in range(0, len(lst), tuple_size)
            ]

        if len(controls) == 1 and isinstance(controls[0], MultipleChoice):
            # Since MultipleChoice widgets are a special case that appear in
            # isolation, our logic to fetch the values out of them is slightly
            # modified from the nominal case presented in the other branch.
            # MultiChoice never appears for multi-value options, only for options
            # where multiple=True.
            control = cast(MultipleChoice, controls[0])
            # control_values =
            # return MultiValueParamData.process_cli_option(control_values)
            raise

        # For each control widget for this parameter, capture the value(s) from them
        collected_values = []
        for control in list(controls):
            control_values = self._get_form_control_value(control)
            collected_values.append(control_values)

        # Since we fetched a flat list of widgets (and thus a flat list of values
        # from those widgets), we now need to group them into tuples based on nargs.
        # We can safely do this since widgets are added to the DOM in the same order
        # as the types specified in the click Option `type`. We convert a flat list
        # of widget values into a list of tuples, each tuple of length nargs.
        collected_values = list_to_tuples(collected_values, self.arg.num_args)
        # return MultiValueParamData.process_cli_option(collected_values)
        raise

    def make_control(self, arg: Arg):
        if arg.action in {ArgAction.store_true, ArgAction.store_false}:
            control = Checkbox(
                arg.value_name,
                button_first=True,
                classes=f"command-form-checkbox {arg.field_name}",
                value=arg.default or False,
            )

        elif arg.choices:
            if arg.multiple:
                control = MultipleChoice(
                    [Text(c) for c in arg.choices],
                    classes=f"command-form-multiple-choice {arg.field_name}",
                    defaults=arg.default,
                )
            else:
                control = Select(
                    [(choice, choice) for choice in arg.choices],
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
        if isinstance(arg.field_name, str):
            text = Text.from_markup(
                f"{arg.field_name}[dim]{' multiple' if arg.multiple else ''} {annotation}[/] {' [b red]*[/]required' if arg.required else ''}"
            )
        else:
            names = Text(" / ", style="dim").join([Text(n) for n in arg.name])
            text = Text.from_markup(
                f"{names}[dim]{' multiple' if arg.multiple else ''} {annotation}[/] {' [b red]*[/]required' if arg.required else ''}"
            )

        return text

    def focus(self, scroll_visible: bool = True):
        if self.first_control is not None:
            self.first_control.focus(scroll_visible)
        return self
