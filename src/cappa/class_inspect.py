from __future__ import annotations

import dataclasses
import functools
import inspect
import typing
from enum import Enum

import typing_inspect
from typing_extensions import Self, get_args

from cappa.typing import MISSING, T, find_type_annotation, get_type_hints, missing

if typing.TYPE_CHECKING:
    pass

__all__ = [
    "fields",
    "detect",
]


def detect(cls: type) -> bool:
    return bool(ClassTypes.from_cls(cls))


@dataclasses.dataclass
class Field:
    name: str
    annotation: type
    default: typing.Any | MISSING = missing
    default_factory: typing.Any | MISSING = missing
    metadata: dict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class DataclassField(Field):
    @classmethod
    def collect(cls, typ: type) -> list[Self]:
        fields = []
        for f in typ.__dataclass_fields__.values():  # type: ignore
            field = cls(
                name=f.name,
                annotation=f.type,
                default=f.default if f.default is not dataclasses.MISSING else missing,
                default_factory=f.default_factory
                if f.default_factory is not dataclasses.MISSING
                else missing,
                metadata=f.metadata,
            )
            fields.append(field)
        return fields


@dataclasses.dataclass
class AttrsField(Field):
    @classmethod
    def collect(cls, typ: type) -> list[Self]:
        fields = []
        for f in typ.__attrs_attrs__:  # type: ignore
            if hasattr(f.default, "factory"):
                default = None
                default_factory = f.default.factory
            else:
                default = f.default
                default_factory = None
            field = cls(
                name=f.name,
                annotation=f.type,
                default=default or missing,
                default_factory=default_factory or missing,
                metadata=f.metadata,
            )
            fields.append(field)
        return fields


@dataclasses.dataclass
class MsgspecField(Field):
    @classmethod
    def collect(cls, typ: type) -> list[Self]:
        import msgspec

        fields = []
        for f in msgspec.structs.fields(typ):
            default = f.default if f.default is not msgspec.NODEFAULT else missing
            default_factory = (
                f.default_factory
                if f.default_factory is not msgspec.NODEFAULT
                else missing
            )
            field = cls(
                name=f.name,
                annotation=f.type,
                default=default,
                default_factory=default_factory,
            )
            fields.append(field)
        return fields


@dataclasses.dataclass
class PydanticV1Field(Field):
    @classmethod
    def collect(cls, typ) -> list[Self]:
        fields = []
        type_hints = get_type_hints(typ, include_extras=True)
        for name, f in typ.__fields__.items():
            annotation = get_type(type_hints[name])

            field = cls(
                name=name,
                annotation=annotation,
                default=f.default
                if f.default.__repr__() != "PydanticUndefined"
                else missing,
                default_factory=f.default_factory or missing,
            )
            fields.append(field)
        return fields


@dataclasses.dataclass
class PydanticV2Field(Field):
    @classmethod
    def collect(cls, typ: type) -> list[Self]:
        fields = []
        for name, f in typ.model_fields.items():  # type: ignore
            field = cls(
                name=name,
                annotation=f.annotation,
                default=f.default
                if f.default.__repr__() != "PydanticUndefined"
                else missing,
                default_factory=f.default_factory or missing,
            )
            fields.append(field)
        return fields


@dataclasses.dataclass
class PydanticV2DataclassField(Field):
    @classmethod
    def collect(cls, typ: type) -> list[Self]:
        fields = []
        for name, f in typ.__pydantic_fields__.items():  # type: ignore
            field = cls(
                name=name,
                annotation=f.annotation,
                default=f.default or missing,
                default_factory=f.default_factory or missing,
            )
            fields.append(field)
        return fields


def fields(cls: type):
    class_type = ClassTypes.from_cls(cls)
    if class_type is None:
        raise ValueError(
            f"'{cls.__qualname__}' is not a currently supported kind of class. "
            "Must be one of: dataclass, pydantic, or attrs class."
        )

    return class_type.value.collect(cls)


class ClassTypes(Enum):
    attrs = AttrsField
    dataclass = DataclassField
    pydantic_v1 = PydanticV1Field
    pydantic_v2 = PydanticV2Field
    pydantic_v2_dataclass = PydanticV2DataclassField
    msgspec = MsgspecField

    @classmethod
    def from_cls(cls, obj: type) -> ClassTypes | None:
        if hasattr(obj, "__pydantic_fields__"):
            return cls.pydantic_v2_dataclass

        if dataclasses.is_dataclass(obj):
            return cls.dataclass

        if hasattr(obj, "__struct_config__"):
            assert obj.__struct_config__.__class__.__module__.startswith("msgspec")
            return cls.msgspec

        try:
            import pydantic
            from pydantic import BaseModel
        except ImportError:  # pragma: no cover
            pass
        else:
            try:
                is_base_model = isinstance(obj, type) and issubclass(obj, BaseModel)
            except TypeError:  # pragma: no cover
                is_base_model = False

            if is_base_model:
                if pydantic.__version__.startswith("1."):
                    return cls.pydantic_v1
                return cls.pydantic_v2

        if hasattr(obj, "__attrs_attrs__"):
            return cls.attrs

        return None


def extract_dataclass_metadata(field: Field, cls: type[T]) -> T | None:
    field_metadata = field.metadata.get("cappa")
    if not field_metadata:
        return None

    if not isinstance(field_metadata, cls):
        return None

    return field_metadata


def get_command_capable_object(obj):
    """Convert raw functions into a stub class.

    Internally, a dataclass is constructed with a `__call__` method which **splats
    the arguments to the dataclass into the original callable.
    """
    if inspect.isfunction(obj):
        from cappa import Dep

        function_args = []

        @functools.wraps(obj)
        def call(self, **deps):
            kwargs = dataclasses.asdict(self)
            return obj(**kwargs, **deps)

        # We need to create a fake signature for the above callable, which does
        # not retain the `Arg` annotations
        sig = inspect.signature(obj)
        sig_params: dict = dict(sig.parameters)
        sig._parameters = sig_params  # type: ignore
        call.__signature__ = sig  # type: ignore

        args = get_type_hints(obj, include_extras=True)
        parameters = inspect.signature(obj).parameters
        for name, annotation in args.items():
            if find_type_annotation(annotation, Dep).obj:
                continue

            sig_params.pop(name, None)
            function_args.append(
                (
                    name,
                    annotation,
                    dataclasses.field(
                        default=parameters[name].default
                        if parameters[name].default is not inspect.Parameter.empty
                        else dataclasses.MISSING
                    ),
                )
            )

        return dataclasses.make_dataclass(
            obj.__name__,
            function_args,
            namespace={"__call__": call},
        )

    return obj


def get_type(typ):
    if typing_inspect.is_optional_type(typ):
        return get_args(typ)[0]
    return typ
