from __future__ import annotations

import sys
import types
import typing
from dataclasses import dataclass, field
from inspect import cleandoc

import typing_extensions
import typing_inspect
from typing_extensions import Annotated, get_args, get_origin
from typing_inspect import is_literal_type

try:
    from typing_extensions import Doc

    doc_type: type | None = Doc
except ImportError:  # pragma: no cover
    doc_type = None

if sys.version_info < (3, 10):
    NoneType = type(None)  # pragma: no cover
else:
    NoneType = types.NoneType  # type: ignore

T = typing.TypeVar("T")

missing = ...
MISSING: typing.TypeAlias = type(missing)  # type: ignore


@dataclass
class ObjectAnnotation(typing.Generic[T]):
    obj: list[T]
    annotation: type
    doc: str | None = None
    other_annotations: list[type] = field(default_factory=list)


def find_type_annotation(type_hint: type, kind: type[T]) -> ObjectAnnotation[T]:
    instances = []
    doc = None

    other_annotations = []
    if get_origin(type_hint) is Annotated:
        annotations = type_hint.__metadata__  # type: ignore
        type_hint = type_hint.__origin__  # type: ignore

        for annotation in annotations:
            is_instance = isinstance(annotation, kind)
            is_kind = isinstance(annotation, type) and issubclass(annotation, kind)

            if is_instance or is_kind:
                instance = annotation
                if is_kind:
                    instance = typing.cast(type, annotation)()

                instances.append(instance)
            else:
                other_annotations.append(annotation)

        if doc_type:
            for annotation in annotations:
                if isinstance(annotation, doc_type):
                    doc = cleandoc(annotation.documentation)  # type: ignore
                    break
        else:
            typing_extensions.assert_never(doc_type)  # type: ignore

    return ObjectAnnotation(
        obj=instances,
        annotation=type_hint,
        doc=doc,
        other_annotations=other_annotations,
    )


def assert_type(value: typing.Any, typ: type[T]) -> T:
    assert isinstance(value, typ), value
    return typing.cast(T, value)


def backend_type(typ) -> str:
    if is_literal_type(typ):
        return get_args(typ)[0]

    return f"<{typ.__name__}>"


def is_union_type(typ):
    if typing_inspect.is_union_type(typ):
        return True

    if hasattr(types, "UnionType") and typ is types.UnionType:
        return True  # pragma: no cover
    return False


def is_none_type(typ):
    return typ is NoneType


def is_subclass(typ, superclass):
    if not isinstance(typ, type):
        return False

    if typ is str:
        return False

    return issubclass(typ, superclass)


def get_optional_type(typ: typing.Optional[T]):
    if typ is NoneType:
        return typ

    args = get_args(typ)
    if len(args) == 2:
        return args[0]

    return typing.Union[args]


def get_type_hints(obj, include_extras=False):
    result = _get_type_hints(obj, include_extras=include_extras)
    if sys.version_info < (3, 11):  # pragma: no cover
        result = fix_annotated_optional_type_hints(result)

    return {k: v for k, v in result.items() if k not in {"return"}}


def fix_annotated_optional_type_hints(
    hints: dict[str, typing.Any],
) -> dict[str, typing.Any]:  # pragma: no cover
    """Normalize `Annotated` interacting with `get_type_hints` in versions <3.11.

    https://github.com/python/cpython/issues/90353.
    """
    for param_name, hint in hints.items():
        args = get_args(hint)
        if (
            get_origin(hint) is typing.Union
            and get_origin(next(iter(args))) is Annotated
        ):
            hints[param_name] = next(iter(args))
    return hints


def is_of_type(annotation, types):
    if typing_inspect.is_optional_type(annotation):
        args = get_args(annotation)
    else:
        args = (annotation,)

    for arg in args:
        arg_annotation = get_origin(arg) or arg
        if is_subclass(arg_annotation, types):
            return True
    return False


if sys.version_info >= (3, 10):
    _get_type_hints = typing.get_type_hints

else:
    from eval_type_backport import eval_type_backport

    @typing.no_type_check
    def _get_type_hints(
        obj: typing.Any,
        globalns: dict[str, typing.Any] | None = None,
        localns: dict[str, typing.Any] | None = None,
        include_extras: bool = False,
    ) -> dict[str, typing.Any]:  # pragma: no cover
        """Backport from python 3.10.8, with exceptions.

        * Use `_forward_ref` instead of `typing.ForwardRef` to handle the `is_class` argument.
        * `eval_type_backport` instead of `eval_type`, to backport syntax changes in Python 3.10.

        https://github.com/python/cpython/blob/aaaf5174241496afca7ce4d4584570190ff972fe/Lib/typing.py#L1773-L1875
        """
        if getattr(obj, "__no_type_check__", None):
            return {}
        # Classes require a special treatment.
        if isinstance(obj, type):
            hints = {}
            for base in reversed(obj.__mro__):
                if globalns is None:
                    base_globals = getattr(
                        sys.modules.get(base.__module__, None), "__dict__", {}
                    )
                else:
                    base_globals = globalns
                ann = base.__dict__.get("__annotations__", {})
                if isinstance(ann, types.GetSetDescriptorType):
                    ann = {}
                base_locals = dict(vars(base)) if localns is None else localns
                if localns is None and globalns is None:
                    # This is surprising, but required.  Before Python 3.10,
                    # get_type_hints only evaluated the globalns of
                    # a class.  To maintain backwards compatibility, we reverse
                    # the globalns and localns order so that eval() looks into
                    # *base_globals* first rather than *base_locals*.
                    # This only affects ForwardRefs.
                    base_globals, base_locals = base_locals, base_globals
                for name, value in ann.items():
                    if value is None:
                        value = type(None)
                    if isinstance(value, str):
                        value = _forward_ref(value, is_argument=False, is_class=True)

                    value = eval_type_backport(value, base_globals, base_locals)
                    hints[name] = value
            if not include_extras and hasattr(typing, "_strip_annotations"):
                return {k: typing._strip_annotations(t) for k, t in hints.items()}
            return hints

        if globalns is None:
            if isinstance(obj, types.ModuleType):
                globalns = obj.__dict__
            else:
                nsobj = obj
                # Find globalns for the unwrapped object.
                while hasattr(nsobj, "__wrapped__"):
                    nsobj = nsobj.__wrapped__
                globalns = getattr(nsobj, "__globals__", {})
            if localns is None:
                localns = globalns
        elif localns is None:
            localns = globalns
        hints = getattr(obj, "__annotations__", None)
        if hints is None:
            # Return empty annotations for something that _could_ have them.
            if isinstance(obj, typing._allowed_types):
                return {}

            raise TypeError(f"{obj!r} is not a module, class, method, " "or function.")
        defaults = typing._get_defaults(obj)
        hints = dict(hints)
        for name, value in hints.items():
            if value is None:
                value = type(None)
            if isinstance(value, str):
                # class-level forward refs were handled above, this must be either
                # a module-level annotation or a function argument annotation

                value = _forward_ref(
                    value,
                    is_argument=not isinstance(obj, types.ModuleType),
                    is_class=False,
                )
            value = eval_type_backport(value, globalns, localns)
            if name in defaults and defaults[name] is None:
                value = typing.Optional[value]
            hints[name] = value
        return (
            hints
            if include_extras
            else {k: typing._strip_annotations(t) for k, t in hints.items()}
        )


def _forward_ref(
    arg: typing.Any,
    is_argument: bool = True,
    *,
    is_class: bool = False,
) -> typing.ForwardRef:
    return typing.ForwardRef(arg, is_argument)
