from __future__ import annotations

import dataclasses
import inspect
import typing
from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING, Any

from typing_extensions import Self

from cappa.type_view import CallableView, Empty, EmptyType
from cappa.typing import T

__all__ = [
    "detect",
    "fields",
]


def detect(cls: type) -> bool:
    return bool(ClassTypes.from_cls(cls))


@dataclasses.dataclass
class Field:
    name: str
    default: typing.Any | EmptyType = Empty
    default_factory: typing.Any | EmptyType = Empty
    metadata: dict[str, Any] = dataclasses.field(default_factory=lambda: {})


@dataclasses.dataclass
class DataclassField(Field):
    @classmethod
    def collect(cls, typ: type) -> list[Self]:
        fields: list[Self] = []
        for f in dataclasses.fields(typ):  # pyright: ignore
            if not f.init:
                continue
            field = cls(
                name=f.name,
                default=f.default if f.default is not dataclasses.MISSING else Empty,
                default_factory=f.default_factory
                if f.default_factory is not dataclasses.MISSING
                else Empty,
                metadata=dict(f.metadata),
            )
            fields.append(field)
        return fields


@dataclasses.dataclass
class AttrsField(Field):
    @classmethod
    def collect(cls, typ: type) -> list[Self]:
        fields: list[Self] = []
        for f in typ.__attrs_attrs__:  # type: ignore
            if hasattr(f.default, "factory"):  # pyright: ignore
                default = None
                default_factory: Any = f.default.factory  # pyright: ignore
            else:
                default = f.default  # pyright: ignore
                default_factory = None
            field = cls(
                name=f.name,  # pyright: ignore
                default=default or Empty,  # pyright: ignore
                default_factory=default_factory or Empty,  # pyright: ignore
                metadata=f.metadata,  # pyright: ignore
            )
            fields.append(field)
        return fields


if TYPE_CHECKING:

    @dataclasses.dataclass
    class MsgspecField(Field):
        @classmethod
        def collect(cls, typ: type) -> list[Self]:
            return []

else:

    @dataclasses.dataclass
    class MsgspecField(Field):
        @classmethod
        def collect(cls, typ: type) -> list[Self]:
            import msgspec  # pyright: ignore

            fields: list[Self] = []
            for f in msgspec.structs.fields(typ):
                default = f.default if f.default is not msgspec.NODEFAULT else Empty
                default_factory = (
                    f.default_factory
                    if f.default_factory is not msgspec.NODEFAULT
                    else Empty
                )
                field = cls(
                    name=f.name,
                    default=default,
                    default_factory=default_factory,
                )
                fields.append(field)
            return fields


@dataclasses.dataclass
class PydanticV1Field(Field):
    @classmethod
    def collect(cls, typ: type) -> list[Self]:
        fields: list[Self] = []
        callable_view = CallableView.from_callable(typ, include_extras=True)
        for param in callable_view.parameters:
            name = param.name
            f = typ.__fields__[name]  # type: ignore

            field = cls(
                name=name,
                default=f.default  # pyright: ignore
                if f.default.__repr__() != "PydanticUndefined"  # pyright: ignore
                else Empty,
                default_factory=f.default_factory or Empty,  # pyright: ignore
            )
            fields.append(field)
        return fields


@dataclasses.dataclass
class PydanticV2Field(Field):
    @classmethod
    def collect(cls, typ: type) -> list[Self]:
        fields: list[Self] = []
        for name, f in typ.model_fields.items():  # type: ignore
            field = cls(
                name=name,  # pyright: ignore
                default=f.default  # pyright: ignore
                if f.default.__repr__() != "PydanticUndefined"  # pyright: ignore
                else Empty,
                default_factory=f.default_factory or Empty,  # pyright: ignore
            )
            fields.append(field)
        return fields


@dataclasses.dataclass
class PydanticV2DataclassField(Field):
    @classmethod
    def collect(cls, typ: type) -> list[Self]:
        fields: list[Self] = []
        for name, f in typ.__pydantic_fields__.items():  # type: ignore
            field = cls(
                name=name,  # pyright: ignore
                default=f.default or Empty,  # pyright: ignore
                default_factory=f.default_factory or Empty,  # pyright: ignore
            )
            fields.append(field)
        return fields


@dataclasses.dataclass
class FunctionField(Field):
    @classmethod
    def collect(cls, typ: type) -> list[Self]:
        params = list(inspect.signature(typ).parameters.items())

        # For method functions, annotate the first param if it's unannotated so the
        # invoke DI system can resolve it as the parent command instance.
        if params and params[0][1].annotation is inspect.Parameter.empty:
            qualname = getattr(typ, "__qualname__", "")
            if "." in qualname:
                parent_name = qualname.rsplit(".", 1)[0]
                parent_cls = getattr(typ, "__globals__", {}).get(parent_name)
                if parent_cls is not None and inspect.isclass(parent_cls):
                    typ.__annotations__[params[0][0]] = parent_cls

        fields: list[Self] = []
        for name, param in params:
            if param.annotation is inspect.Parameter.empty:
                continue
            field = cls(
                name=name,
                default=param.default
                if param.default is not inspect.Parameter.empty
                else Empty,
                default_factory=Empty,
            )
            fields.append(field)
        return fields


def fields(cls: type | Callable[..., Any]):
    class_type = ClassTypes.from_cls(cls)
    if class_type is None:
        raise ValueError(
            f"'{cls.__qualname__}' is not a currently supported kind of class. "
            "Must be one of: dataclass, pydantic, or attrs class."
        )

    return class_type.value.collect(cls)  # pyright: ignore


class ClassTypes(Enum):
    attrs = AttrsField
    dataclass = DataclassField
    pydantic_v1 = PydanticV1Field
    pydantic_v2 = PydanticV2Field
    pydantic_v2_dataclass = PydanticV2DataclassField
    msgspec = MsgspecField
    function = FunctionField

    @classmethod
    def from_cls(cls, obj: type | Callable[..., Any]) -> ClassTypes | None:
        if inspect.isfunction(obj):
            return cls.function

        if hasattr(obj, "__pydantic_fields__"):
            return cls.pydantic_v2_dataclass

        if dataclasses.is_dataclass(obj):
            return cls.dataclass

        if hasattr(obj, "__struct_config__"):  # pyright: ignore
            assert obj.__struct_config__.__class__.__module__.startswith("msgspec")  # pyright: ignore
            return cls.msgspec

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
                    return cls.pydantic_v1
                return cls.pydantic_v2

        if hasattr(obj, "__attrs_attrs__"):  # pyright: ignore
            return cls.attrs

        return None


def extract_dataclass_metadata(field: Field, cls: type[T]) -> list[T]:
    field_metadata = field.metadata.get("cappa")
    if not field_metadata:
        return []

    if not isinstance(field_metadata, cls):
        return []

    return [field_metadata]
