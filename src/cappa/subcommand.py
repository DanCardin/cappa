from __future__ import annotations

import dataclasses
import typing

from typing_extensions import Self
from typing_inspect import is_optional_type, is_union_type

from cappa.class_inspect import Field, extract_dataclass_metadata
from cappa.typing import MISSING, T, find_type_annotation

if typing.TYPE_CHECKING:
    from cappa.command import Command


@dataclasses.dataclass
class Subcommand:
    """Describe a CLI subcommand.

    Arguments:
        name: Defaults to the name of the class, converted to dash case, but
            can be overridden here.
        help: By default, the help text will be inferred from the containing class'
            arguments' section, if it exists. Alternatively, you can directly supply
            the help text here.
        types: Defaults to the class's annotated types, but can be overridden here.
        required: Defaults to automatically inferring requiredness, based on whether the
            class's value has a default. By setting this, you can force a particular value.
    """

    name: str | MISSING = ...
    help: str = ""
    types: typing.Iterable[type] | MISSING = ...
    required: bool | None = None

    @classmethod
    def collect(cls, field: Field, type_hint: type) -> Self | None:
        subcommand, annotation = find_type_annotation(type_hint, cls)
        field_metadata = extract_dataclass_metadata(field)
        if field_metadata:
            if not isinstance(field_metadata, Subcommand):
                return None

            subcommand = field_metadata  # type: ignore

        if subcommand is None:
            return None

        has_none = False
        kwargs: dict[str, typing.Any] = {}
        if subcommand.types is ...:
            if is_union_type(annotation):
                types = typing.get_args(annotation)
                if is_optional_type(annotation):
                    has_none = True
                    types = tuple([t for t in types if not is_optional_type(t)])
            else:
                types = (annotation,)

            kwargs["types"] = types

        if subcommand.required is None:
            kwargs["required"] = not has_none

        kwargs["name"] = field.name

        return dataclasses.replace(subcommand, **kwargs)


@dataclasses.dataclass
class Subcommands(typing.Generic[T]):
    name: str
    options: dict[str, Command]
    required: bool
    help: str

    def map_result(self, parsed_args):
        option_name = parsed_args.pop("__name__")
        option = self.options[option_name]
        return option.map_result(option, parsed_args)
