import sys
import typing

from cappa.command import Command
from cappa.command_def import CommandDefinition

T = typing.TypeVar("T")


def parse(
    obj: type[T],
    *,
    argv: list[str] | None = None,
    render: typing.Callable | None = None,
    exit_with=None,
) -> T:
    if argv is None:
        argv = sys.argv

    instance = Command.get(obj)
    return CommandDefinition.parse(
        instance,
        argv=argv,
        render=render,
        exit_with=exit_with,
    )


def invoke(
    obj: type,
    *,
    argv: list[str] | None = None,
    render: typing.Callable | None = None,
    exit_with=None,
):
    if argv is None:
        argv = sys.argv

    instance: Command = Command.get(obj)
    return CommandDefinition.invoke(
        instance,
        argv=argv,
        render=render,
        exit_with=exit_with,
    )
