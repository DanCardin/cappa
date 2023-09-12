from __future__ import annotations

import dataclasses
import typing
from collections.abc import Callable
from typing import Protocol

from typing_extensions import Self

T = typing.TypeVar("T")


@dataclasses.dataclass
class Command(typing.Generic[T]):
    cls: typing.Type[T]
    name: str | None = None
    help: str | None = None
    invoke: Callable | str | None = None

    @classmethod
    def get(cls, obj: typing.Type[T]) -> Self:
        return getattr(obj, "__cappa__", cls(obj))

    def real_name(self) -> str:
        if self.name is not None:
            return self.name

        cls_name = self.cls.__name__
        import re

        return re.sub(r"(?<!^)(?=[A-Z])", "-", cls_name).lower()

    @classmethod
    def wrap(
        cls,
        _decorated_cls=None,
        *,
        name=None,
        help=None,
        invoke: Callable | None = None,
    ):
        def wrapper(_decorated_cls):
            instance = cls(cls=_decorated_cls, invoke=invoke, name=name, help=help)
            _decorated_cls.__cappa__ = instance
            return _decorated_cls

        if _decorated_cls is None:
            return wrapper
        return wrapper(_decorated_cls)


H = typing.TypeVar("H", covariant=True)


class HasCommand(typing.Generic[H], Protocol):
    __cappa__: typing.ClassVar[Command]
