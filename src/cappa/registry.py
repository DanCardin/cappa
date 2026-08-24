from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from cappa.command import Command


class Registry:
    """Maps decorated classes/functions to their Command configuration."""

    def __init__(self) -> None:
        self._registry: dict[Any, Command[Any]] = {}

    def register(self, obj: Any, command: Command[Any]) -> None:
        self._registry[obj] = command

    def get(self, obj: Any) -> Command[Any] | None:
        return self._registry.get(obj)

    def __contains__(self, obj: Any) -> bool:
        return obj in self._registry


default_registry: Registry = Registry()
