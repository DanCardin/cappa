from __future__ import annotations

import dataclasses
import functools
import inspect
import sys
import typing
from enum import Enum

from typing_extensions import Annotated, Self

from cappa.type_view import CallableView, Empty, EmptyType
from cappa.typing import T, find_annotations

if typing.TYPE_CHECKING:
    from cappa.command import Command

__all__ = [
    "detect",
    "fields",
]


def detect(cls: type) -> bool:
    return bool(ClassTypes.from_cls(cls))


@dataclasses.dataclass
class Field:
    name: str
    annotation: type
    default: typing.Any | EmptyType = Empty
    default_factory: typing.Any | EmptyType = Empty
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
                default=f.default if f.default is not dataclasses.MISSING else Empty,
                default_factory=f.default_factory
                if f.default_factory is not dataclasses.MISSING
                else Empty,
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
                default=default or Empty,
                default_factory=default_factory or Empty,
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
            default = f.default if f.default is not msgspec.NODEFAULT else Empty
            default_factory = (
                f.default_factory
                if f.default_factory is not msgspec.NODEFAULT
                else Empty
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
        callable_view = CallableView.from_callable(typ, include_extras=True)
        for param in callable_view.parameters:
            name = param.name
            f = typ.__fields__[name]
            annotation = param.type_view.strip_optional().annotation

            field = cls(
                name=name,
                annotation=annotation,
                default=f.default
                if f.default.__repr__() != "PydanticUndefined"
                else Empty,
                default_factory=f.default_factory or Empty,
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
                else Empty,
                default_factory=f.default_factory or Empty,
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
                default=f.default or Empty,
                default_factory=f.default_factory or Empty,
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


def extract_dataclass_metadata(field: Field, cls: type[T]) -> list[T]:
    field_metadata = field.metadata.get("cappa")
    if not field_metadata:
        return []

    if not isinstance(field_metadata, cls):
        return []

    return [field_metadata]


def get_command_capable_object(obj):
    """Convert raw functions into a stub class.

    Internally, a dataclass is constructed with a `__call__` method which **splats
    the arguments to the dataclass into the original callable.
    """
    if inspect.isfunction(obj):
        from cappa import Dep

        function_args = []

        @functools.wraps(obj)
        def call(self, *args, **deps):
            kwargs = dataclasses.asdict(self)
            return obj(*args, **kwargs, **deps)

        callable_view = CallableView.from_callable(obj, include_extras=True)

        # We need to create a fake signature for the above callable, which does
        # not retain the `Arg` annotations
        signature = callable_view.signature
        sig_params: dict = dict(signature.parameters)
        signature._parameters = sig_params  # type: ignore
        call.__signature__ = signature  # type: ignore

        for param_view in callable_view.parameters:
            if not param_view.has_annotation:
                continue

            if find_annotations(param_view.type_view, Dep):
                continue

            sig_params.pop(param_view.name, None)
            function_args.append(
                (
                    param_view.name,
                    param_view.type_view.raw,
                    dataclasses.field(
                        default=param_view.default
                        if param_view.has_default
                        else dataclasses.MISSING
                    ),
                )
            )

        result = dataclasses.make_dataclass(
            obj.__name__,
            function_args,
            namespace={"__call__": call},
        )
        result.__doc__ = obj.__doc__
        result.__cappa__ = getattr(obj, "__cappa__", None)  # type: ignore
        return result

    method_subcommands = collect_method_subcommands(obj)
    if method_subcommands:
        from cappa.subcommand import Subcommand

        kw_only: dict[str, typing.Any] = {}
        if sys.version_info >= (3, 10):
            kw_only["kw_only"] = True

        return dataclasses.make_dataclass(
            obj.__name__,
            [
                (
                    "__cappa_subcommand__",
                    Annotated[
                        typing.Union[method_subcommands],  # pyright: ignore
                        Subcommand("command", required=True),
                    ],
                    dataclasses.field(
                        repr=False, compare=False, default=None, **kw_only
                    ),
                ),
            ],
            bases=(obj,),
        )

    return obj


def collect_method_subcommands(cls: type) -> tuple[typing.Callable, ...]:
    return tuple(
        method
        for _, method in inspect.getmembers(cls, callable)
        if hasattr(method, "__cappa__")
    )


def has_command(obj) -> bool:
    return hasattr(obj, "__cappa__")


def get_command(obj) -> Command | None:
    return getattr(obj, "__cappa__", None)
