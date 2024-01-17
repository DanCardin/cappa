from __future__ import annotations

import dataclasses
import inspect
import typing
from enum import Enum

import typing_inspect
from typing_extensions import Self, get_args

from cappa.typing import MISSING, get_type_hints, missing

if typing.TYPE_CHECKING:
    from cappa import Arg, Subcommand

__all__ = [
    "fields",
    "detect",
]


def detect(cls: type) -> bool:
    try:
        return bool(ClassTypes.from_cls(cls))
    except ValueError:
        return False


class ClassTypes(Enum):
    attrs = "attrs"
    dataclass = "dataclass"
    pydantic_v1 = "pydantic_v1"
    pydantic_v2 = "pydantic_v2"
    pydantic_v2_dataclass = "pydantic_v2_dataclass"

    @classmethod
    def from_cls(cls, obj: type) -> ClassTypes:
        if hasattr(obj, "__pydantic_fields__"):
            return cls.pydantic_v2_dataclass

        if dataclasses.is_dataclass(obj):
            return cls.dataclass

        try:
            import pydantic
        except ImportError:  # pragma: no cover
            pass
        else:
            try:
                is_base_model = isinstance(obj, type) and issubclass(
                    obj, pydantic.BaseModel
                )
            except TypeError:  # pragma: no cover
                is_base_model = False

            if is_base_model:
                if pydantic.__version__.startswith("1."):
                    return cls.pydantic_v1
                return cls.pydantic_v2

        if hasattr(obj, "__attrs_attrs__"):
            return cls.attrs

        raise ValueError(
            f"'{obj.__qualname__}' is not a currently supported kind of class. "
            "Must be one of: dataclass, pydantic, or attrs class."
        )


@dataclasses.dataclass
class Field:
    name: str
    annotation: type
    default: typing.Any | MISSING = missing
    default_factory: typing.Any | MISSING = missing
    metadata: dict = dataclasses.field(default_factory=dict)

    @classmethod
    def from_dataclass(cls, typ: type) -> list[Self]:
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

    @classmethod
    def from_pydantic_v1(cls, typ) -> list[Self]:
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

    @classmethod
    def from_pydantic_v2(cls, typ: type) -> list[Self]:
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

    @classmethod
    def from_pydantic_v2_dataclass(cls, typ: type) -> list[Self]:
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

    @classmethod
    def from_attrs(cls, typ: type) -> list[Self]:
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


def fields(cls: type):
    class_type = ClassTypes.from_cls(cls)
    if class_type == ClassTypes.dataclass:
        return Field.from_dataclass(cls)

    if class_type == ClassTypes.pydantic_v1:
        return Field.from_pydantic_v1(cls)

    if class_type == ClassTypes.pydantic_v2:
        return Field.from_pydantic_v2(cls)

    if class_type == ClassTypes.pydantic_v2_dataclass:
        return Field.from_pydantic_v2_dataclass(cls)

    if class_type == ClassTypes.attrs:
        return Field.from_attrs(cls)

    raise NotImplementedError()  # pragma: no cover


def extract_dataclass_metadata(field: Field) -> Arg | Subcommand | None:
    from cappa.arg import Arg
    from cappa.subcommand import Subcommand

    field_metadata = field.metadata.get("cappa")
    if not field_metadata:
        return None

    if not isinstance(field_metadata, (Arg, Subcommand)):
        raise ValueError(
            '`metadata={"cappa": <x>}` must be of type `Arg` or `Subcommand`'
        )

    return field_metadata


def get_command_capable_object(obj):
    """Convert raw functions into a stub class.

    Internally, a dataclass is constructed with a `__call__` method which **splats
    the arguments to the dataclass into the original callable.
    """
    if inspect.isfunction(obj):

        def call(self):
            kwargs = dataclasses.asdict(self)
            return obj(**kwargs)

        args = get_type_hints(obj, include_extras=True)
        parameters = inspect.signature(obj).parameters
        fields = [
            (
                name,
                annotation,
                dataclasses.field(
                    default=parameters[name].default
                    if parameters[name].default is not inspect.Parameter.empty
                    else dataclasses.MISSING
                ),
            )
            for name, annotation in args.items()
        ]
        return dataclasses.make_dataclass(
            obj.__name__,
            fields,
            namespace={"__call__": call},
        )

    return obj


def get_type(typ):
    if typing_inspect.is_optional_type(typ):
        return get_args(typ)[0]
    return typ
