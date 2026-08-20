from __future__ import annotations

import dataclasses
import inspect
import typing
from collections.abc import Callable
from typing import Any, cast

from cappa.type_view import Empty, EmptyType
from cappa.typing import T

__all__ = [
    "detect",
    "extract_dataclass_metadata",
    "fields",
]


@dataclasses.dataclass
class Field:
    name: str
    default: typing.Any | EmptyType = Empty
    default_factory: typing.Any | EmptyType = Empty
    metadata: dict[str, Any] = dataclasses.field(default_factory=lambda: {})


def detect(cls: type) -> bool:
    return _detect_collector(cls) is not None


def fields(cls: type | Callable[..., Any]) -> list[Field]:
    collector = _detect_collector(cls)
    if collector is None:
        raise ValueError(
            f"'{cls.__qualname__}' is not a currently supported kind of class. "
            "Must be one of: dataclass, pydantic, or attrs class."
        )
    return collector(cls)


def extract_dataclass_metadata(field: Field, cls: type[T]) -> list[T]:
    field_metadata = field.metadata.get("cappa")
    if not field_metadata:
        return []

    if not isinstance(field_metadata, cls):
        return []

    return [field_metadata]


def _detect_collector(
    obj: type | Callable[..., Any],
) -> Callable[[type | Callable[..., Any]], list[Field]] | None:
    if inspect.isfunction(obj):
        return _collect_function  # type: ignore

    assert isinstance(obj, type)
    if hasattr(obj, "__pydantic_fields__"):
        return _collect_pydantic_v2_dataclass  # type: ignore

    if dataclasses.is_dataclass(obj):
        return _collect_dataclass  # type: ignore

    if hasattr(obj, "__struct_config__"):  # pyright: ignore
        assert obj.__struct_config__.__class__.__module__.startswith("msgspec")  # pyright: ignore
        return _collect_msgspec  # type: ignore

    try:
        import pydantic  # pyright: ignore
        from pydantic import BaseModel  # pyright: ignore
    except ImportError:  # pragma: no cover
        pass
    else:
        try:
            is_base_model = isinstance(obj, type) and issubclass(obj, BaseModel)
        except TypeError:  # pragma: no cover
            is_base_model = False

        if is_base_model:
            if getattr(pydantic, "__version__", "1.0").startswith("1."):  # pyright: ignore, pragma: no cover
                return _collect_pydantic_v1  # type: ignore
            return _collect_pydantic_v2  # type: ignore

    if hasattr(obj, "__attrs_attrs__"):  # pyright: ignore
        return _collect_attrs  # type: ignore

    return None


def _collect_dataclass(typ: type) -> list[Field]:
    result: list[Field] = []
    for f in dataclasses.fields(typ):  # pyright: ignore
        if not f.init:
            continue
        result.append(
            Field(
                name=f.name,
                default=f.default if f.default is not dataclasses.MISSING else Empty,
                default_factory=f.default_factory
                if f.default_factory is not dataclasses.MISSING
                else Empty,
                metadata=dict(f.metadata),
            )
        )
    return result


def _collect_attrs(typ: type) -> list[Field]:
    result: list[Field] = []
    for f in typ.__attrs_attrs__:  # type: ignore
        if hasattr(f.default, "factory"):  # pyright: ignore
            default = None
            default_factory: Any = f.default.factory  # pyright: ignore
        else:
            default = f.default  # pyright: ignore
            default_factory = None
        result.append(
            Field(
                name=f.name,  # pyright: ignore
                default=default or Empty,  # pyright: ignore
                default_factory=default_factory or Empty,  # pyright: ignore
                metadata=f.metadata,  # pyright: ignore
            )
        )
    return result


def _collect_msgspec(typ: type) -> list[Field]:
    import msgspec as _msgspec  # pyright: ignore

    msgspec = cast(Any, _msgspec)
    result: list[Field] = []
    for f in msgspec.structs.fields(typ):
        result.append(
            Field(
                name=f.name,
                default=f.default if f.default is not msgspec.NODEFAULT else Empty,
                default_factory=f.default_factory
                if f.default_factory is not msgspec.NODEFAULT
                else Empty,
            )
        )
    return result


def _collect_pydantic_v1(typ: type) -> list[Field]:
    from cappa.type_view import CallableView

    result: list[Field] = []
    callable_view = CallableView.from_callable(typ, include_extras=True)
    for param in callable_view.parameters:
        name = param.name
        f = typ.__fields__[name]  # type: ignore
        result.append(
            Field(
                name=name,
                default=f.default  # pyright: ignore
                if f.default.__repr__() != "PydanticUndefined"  # pyright: ignore
                else Empty,
                default_factory=f.default_factory or Empty,  # pyright: ignore
            )
        )
    return result


def _collect_pydantic_v2(typ: type) -> list[Field]:
    result: list[Field] = []
    for name, f in typ.model_fields.items():  # type: ignore
        result.append(
            Field(
                name=cast(str, name),
                default=f.default  # pyright: ignore
                if f.default.__repr__() != "PydanticUndefined"  # pyright: ignore
                else Empty,
                default_factory=f.default_factory or Empty,  # pyright: ignore
            )
        )
    return result


def _collect_pydantic_v2_dataclass(typ: type) -> list[Field]:
    result: list[Field] = []
    for name, f in typ.__pydantic_fields__.items():  # type: ignore
        result.append(
            Field(
                name=cast(str, name),
                default=f.default or Empty,  # pyright: ignore
                default_factory=f.default_factory or Empty,  # pyright: ignore
            )
        )
    return result


def _collect_function(typ: type) -> list[Field]:
    params = list(inspect.signature(typ).parameters.items())

    if params and params[0][1].annotation is inspect.Parameter.empty:
        qualname = getattr(typ, "__qualname__", "")
        if "." in qualname:
            parent_name = qualname.rsplit(".", 1)[0]
            parent_cls = getattr(typ, "__globals__", {}).get(parent_name)
            if parent_cls is not None and inspect.isclass(parent_cls):
                typ.__annotations__[params[0][0]] = parent_cls

    result: list[Field] = []
    for name, param in params:
        if param.annotation is inspect.Parameter.empty:
            continue
        result.append(
            Field(
                name=name,
                default=param.default
                if param.default is not inspect.Parameter.empty
                else Empty,
                default_factory=Empty,
            )
        )
    return result
