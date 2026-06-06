from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Generic, TextIO, TypeVar

from type_lens import TypeView
from typing_extensions import Annotated

from cappa.arg import FinalArg
from cappa.default import Default
from cappa.invoke.types import Resolved
from cappa.output import Output
from cappa.state import State


@dataclass(frozen=True)
class Destructure:
    """Collection for destructuring settings."""

    @classmethod
    def collect(
        cls,
        field_name: str,
        default: Default,
        destructure: Destructure | bool | None,
        type_view: TypeView[Any],
    ) -> FinalDestructure[Any] | None:
        if not destructure:
            return None

        if destructure is True:
            destructure = Destructure()

        annotation = type_view.strip_optional().annotation
        if not isinstance(annotation, type):
            raise ValueError(
                "Destructured arguments currently only support singular concrete types."
            )

        command: FinalCommand[Any] = Command.get(annotation).collect()  # pyright: ignore
        return FinalDestructure(
            field_name=field_name,
            command=command,
            is_optional=type_view.is_optional,
            default=default,
        )


T = TypeVar("T")
Destructured = Annotated[T, Destructure()]


@dataclass(frozen=True)
class FinalDestructure(Destructure, Generic[T]):
    """Post-normalization representation of a destructured argument.

    This is produced alongside FinalArg/FinalSubcommand in a `Command`'s set of arguments.
    The parser and mapper work together to produce the destructured value as a nested mapping
    that the contained virtual `command` can understand, and then the result is mapped to
    the final value of the field.
    """

    field_name: str
    command: FinalCommand[T]
    is_optional: bool
    default: Default

    def map_result(
        self,
        prog: str,
        parsed_args: dict[str, Any],
        output: Output,
        state: State[Any] | None = None,
        input: TextIO | None = None,
    ) -> Resolved[T]:
        if self.is_optional and not parsed_args:
            _, value = self.default(state=state, input=input)
            return Resolved(lambda: value)

        return self.command.map_result(
            self.command, prog, parsed_args, output, state, input
        )[0]

    def explode_args(self) -> list[FinalArg[Any] | FinalDestructure[Any]]:
        virtual_args = self.command.arguments

        result: list[FinalArg[Any] | FinalDestructure[Any]] = [self]
        for virtual_arg in virtual_args:
            if not isinstance(virtual_arg, FinalArg):
                raise ValueError(
                    "Only `Arg` is supported in the context of a destructured argument"
                )

            virtual_arg = replace(
                virtual_arg,
                destructure=self,
                has_value=False,
            )

            result.append(virtual_arg)

        return result


from cappa.command import Command, FinalCommand  # noqa: E402
