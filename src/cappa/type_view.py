from type_lens import CallableView, Empty, EmptyType, TypeView

__all__ = [
    "CallableView",
    "Empty",
    "EmptyType",
    "TypeView",
    "optional_repr_type",
]


def optional_repr_type(type_view: TypeView) -> str:
    if type_view.annotation:
        return type_view.repr_type
    return "<empty>"
