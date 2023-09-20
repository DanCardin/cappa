from __future__ import annotations

import dataclasses
import typing
from collections.abc import Callable
from typing import Protocol

from typing_extensions import Self

T = typing.TypeVar("T")


@dataclasses.dataclass
class Command(typing.Generic[T]):
    """Register a cappa CLI command/subcomment.

    Args:
        cmd_cls: The class representing the command/subcommand
        name: The name of the command. If omitted, the name of the command
            will be the name of the `cls`, converted to dash-case.
        help: Optional help text. If omitted, the `cls` docstring will be parsed.
            The headline/description sections will be used to document the command
            itself, and the arguments section will become the default help text for
            any params/options.
        invoke: Optional command to be called in the event parsing is successful.
            In the case of subcommands, it will only call the parsed/selected
            function to invoke. The value can **either** be a callable object or
            a string. When the value is a string it will be interpreted as
            `module.submodule.function`; the module will be dynamically imported,
            and the referenced function invoked.
    """

    cmd_cls: typing.Type[T]
    name: str | None = None
    help: str | None = None
    invoke: Callable | str | None = None

    @classmethod
    def wrap(
        cls,
        *,
        name=None,
        help=None,
        invoke: Callable | str | None = None,
    ):
        """Register a cappa CLI command/subcomment.

        Args:
            cls: The class representing the command/subcommand
            name: The name of the command. If omitted, the name of the command
                will be the name of the `cls`, converted to dash-case.
            help: Optional help text. If omitted, the `cls` docstring will be parsed.
                The headline/description sections will be used to document the command
                itself, and the arguments section will become the default help text for
                any params/options.
            invoke: Optional command to be called in the event parsing is successful.
                In the case of subcommands, it will only call the parsed/selected
                function to invoke.
        """

        def wrapper(_decorated_cls):
            instance = cls(cmd_cls=_decorated_cls, invoke=invoke, name=name, help=help)
            _decorated_cls.__cappa__ = instance
            return _decorated_cls

        return wrapper

    @classmethod
    def get(cls, obj: typing.Type[T]) -> Self:
        return getattr(obj, "__cappa__", cls(obj))

    def real_name(self) -> str:
        if self.name is not None:
            return self.name

        cls_name = self.cmd_cls.__name__
        import re

        return re.sub(r"(?<!^)(?=[A-Z])", "-", cls_name).lower()


H = typing.TypeVar("H", covariant=True)


class HasCommand(typing.Generic[H], Protocol):
    __cappa__: typing.ClassVar[Command]
