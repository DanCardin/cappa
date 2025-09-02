from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Hashable, TypeVar

from type_lens import TypeView
from typing_extensions import Annotated

from cappa.output import Output
from cappa.typing import assert_type

if TYPE_CHECKING:
    from cappa.arg import Arg, ArgActionType


@dataclass(frozen=True)
class Destructure:
    """Collection for destructuring settings."""


T = TypeVar("T")
Destructured = Annotated[T, Destructure()]


def destructure(arg: Arg[Any], type_view: TypeView[Any]) -> list[Arg[Any]]:
    annotation = type_view.strip_optional().annotation
    if not isinstance(annotation, type):
        raise ValueError(
            "Destructured arguments currently only support singular concrete types."
        )

    command: Command[Any] = Command.collect(Command.get(annotation))  # pyright: ignore
    virtual_args = command.arguments

    def _parse_destructured(value: dict[str, Any]):
        return command.cmd_cls(**value)

    arg = replace(arg, parse=_parse_destructured)

    result = [arg]
    for virtual_arg in virtual_args:
        if isinstance(virtual_arg, Subcommand):
            raise ValueError(
                "Subcommands are unsupported in the context of a destructured argument"
            )

        assert virtual_arg.action
        virtual_arg = replace(
            virtual_arg,
            action=restructure(arg, virtual_arg.action),
            has_value=False,
        )

        result.append(virtual_arg)

    return result


def restructure(root_arg: Arg[Any], action: ArgActionType):
    action_handler = determine_action_handler(action)

    def restructure_action(
        parse_state: ParseState, context: ParseContext, arg: Arg[Any], value: Value[Any]
    ):
        root_field_name = assert_type(root_arg.field_name, str)
        result = context.result.setdefault(root_field_name, {})
        nested_context = replace(context, result=result)

        fulfilled_deps: dict[Hashable, Any] = {
            Command: parse_state.current_command,
            Output: parse_state.output,
            ParseContext: nested_context,
            Arg: arg,
            Value: value,
        }
        deps = fulfill_deps(action_handler, fulfilled_deps)
        action_result = action_handler(**deps.kwargs)

        assert arg.parse
        assert callable(arg.parse)
        result[arg.field_name] = arg.parse(action_result)
        return result

    return restructure_action


from cappa.arg import Arg  # noqa: E402
from cappa.command import Command  # noqa: E402
from cappa.invoke import fulfill_deps  # noqa: E402
from cappa.parser import (  # noqa: E402
    ParseContext,
    ParseState,
    Value,
    determine_action_handler,
)
from cappa.subcommand import Subcommand  # noqa: E402
