from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, Callable, cast

if TYPE_CHECKING:
    from cappa.command import Command


class Registry:
    """Maps decorated classes/functions to their Command configuration."""

    def __init__(self) -> None:
        self._registry: dict[Any, Command[Any]] = {}
        self._method_registry: dict[tuple[str, str], list[Callable[..., Any]]] = {}
        self._dep_signatures: dict[Any, inspect.Signature] = {}

    def register(self, obj: Any, command: Command[Any]) -> None:
        self._registry[obj] = command

    def register_method(self, fn: Callable[..., Any]) -> None:
        """Record a decorated method against its parent class (by module + qualname)."""
        qualname = getattr(fn, "__qualname__", "")
        if "." not in qualname:
            return
        parent_qualname = qualname.rsplit(".", 1)[0]
        key = (getattr(fn, "__module__", ""), parent_qualname)
        self._method_registry.setdefault(key, []).append(fn)

    def method_subcommands(
        self, cls: type | Callable[..., Any]
    ) -> tuple[Callable[..., Any], ...]:
        """Return method subcommands registered for *cls* at decoration time."""
        key = (getattr(cls, "__module__", ""), cls.__qualname__)
        methods = self._method_registry.get(key, [])
        if not inspect.isclass(cls):
            return tuple(methods)

        # Distinct classes from a factory can share a module and qualname.
        # Inspect raw members so descriptors are not bound during collection.
        member_ids = {
            id(cast(Any, member).__func__)
            if isinstance(member, (staticmethod, classmethod))
            else id(member)
            for member in vars(cls).values()
        }
        return tuple(method for method in methods if id(method) in member_ids)

    def register_dep_signature(self, fn: Any, signature: inspect.Signature) -> None:
        self._dep_signatures[fn] = signature

    def get_dep_signature(
        self, fn: Any, cli_names: set[str]
    ) -> inspect.Signature | None:
        signature = self._dep_signatures.get(fn)
        if signature is None:
            return None
        dep_params = [
            p for name, p in signature.parameters.items() if name not in cli_names
        ]
        return signature.replace(parameters=dep_params)

    def get(self, obj: Any) -> Command[Any] | None:
        return self._registry.get(obj)

    def __contains__(self, obj: Any) -> bool:
        return obj in self._registry


default_registry: Registry = Registry()
