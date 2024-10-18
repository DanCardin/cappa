from __future__ import annotations

import ast
import inspect
import textwrap
import typing
from dataclasses import dataclass
from types import ModuleType

from typing_extensions import Self

try:
    import docstring_parser as _docstring_parser

    docstring_parser: ModuleType | None = _docstring_parser
except ImportError:  # pragma: no cover
    docstring_parser = None


@dataclass
class ClassHelpText:
    summary: str | None
    body: str | None
    args: dict[str, str]

    @classmethod
    def collect(cls, command: type) -> Self:
        args = {}

        doc = get_doc(command)
        if docstring_parser:
            parsed_help = docstring_parser.parse(doc)
            for param in parsed_help.params:
                args[param.arg_name] = param.description
            summary = parsed_help.short_description
            body = parsed_help.long_description
        else:
            doc = inspect.cleandoc(doc).split("\n", 1)
            if len(doc) == 1:
                summary = doc[0]
                body = ""
            else:
                summary, body = doc
                body = body.strip()

        try:
            ast_args = get_attribute_docstrings(command)
        except Exception:
            ast_args = {}

        args.update(ast_args)

        return cls(summary=summary, body=body, args=args)


def get_doc(cls):
    """Lifted from dataclasses source."""
    doc = cls.__doc__ or ""

    # Dataclasses will set the doc attribute to the below value if there was no
    # explicit docstring. This is just annoying for us, so we treat that as though
    # there wasn't one.
    try:
        # In some cases fetching a signature is not possible.
        # But, we surely should not fail in this case.
        text_sig = str(inspect.signature(cls)).replace(" -> None", "")
    except (TypeError, ValueError):  # pragma: no cover
        text_sig = ""

    dataclasses_docstring = cls.__name__ + text_sig

    if doc == dataclasses_docstring:
        return ""
    return doc


def get_attribute_docstrings(command: type) -> dict[str, str]:
    result: dict[str, str] = {}

    raw_source = inspect.getsource(command)
    source = textwrap.dedent(raw_source)
    module = ast.parse(source)

    cls_node = module.body[-1]
    assert isinstance(cls_node, ast.ClassDef)

    last_assignment: ast.AnnAssign | None = None
    for node in cls_node.body:
        if isinstance(node, ast.Expr):
            if last_assignment:
                name = typing.cast(ast.Name, last_assignment.target).id
                value = typing.cast(ast.Constant, node.value).value
                result[name] = value
                continue

        last_assignment = node if isinstance(node, ast.AnnAssign) else None

    return result
