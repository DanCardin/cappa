from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from type_lens import TypeView

from cappa.output import Output

if TYPE_CHECKING:
    from cappa.final import ArgActionType, FinalArg


@dataclass
class Destructured: ...


def destructure(arg: FinalArg, type_view: TypeView):
    from cappa.command import Command

    if not isinstance(type_view.annotation, type):
        raise ValueError(
            "Destructured arguments currently only support singular concrete types."
        )

    command: Command = Command.get(type_view.annotation)
    command = Command.collect(command)

    arg = replace(arg, parse=lambda v: command.cmd_cls(**v))

    result = [arg]
    for virtual_arg in command.value_arguments:
        virtual_arg = replace(
            virtual_arg,
            action=restructure(arg, virtual_arg.action),
            has_value=False,
        )

        result.append(virtual_arg)

    return result


def restructure(root_arg: FinalArg, action: ArgActionType):
    from cappa.command import Command
    from cappa.final import FinalArg
    from cappa.invoke import fulfill_deps
    from cappa.parser import ParseContext, ParseState, Value, determine_action_handler

    action_handler = determine_action_handler(action)

    def restructure_action(
        parse_state: ParseState, context: ParseContext, arg: FinalArg, value: Value
    ):
        result = context.result.setdefault(root_arg.field_name, {})

        fulfilled_deps: dict = {
            Command: parse_state.current_command,
            Output: parse_state.output,
            ParseContext: context,
            FinalArg: arg,
            Value: value,
        }
        deps = fulfill_deps(action_handler, fulfilled_deps)
        action_result = action_handler(**deps.kwargs)

        result[arg.field_name] = arg.parse(action_result)
        return result

    return restructure_action
