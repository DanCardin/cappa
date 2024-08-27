from dataclasses import dataclass
from typing import Union
from unittest.mock import Mock

import pytest
from docutils.core import publish_from_doctree
from docutils.parsers.rst.states import Body, RSTStateMachine
from docutils.utils import new_document
from typing_extensions import Annotated

import cappa
from cappa.ext.docutils import CappaDirective


@dataclass
class Foo:
    bar: int
    baz: Annotated[int, cappa.Arg(help="asdf")]


@cappa.command(help="has help", description="has description")
@dataclass
class Bar:
    bar: int = 4


@dataclass
class Subcommand:
    subcmd: cappa.Subcommands[Union[Bar, Foo]]


def create_directive(*, style, cls_name="Foo", terminal_width=0):
    state = Body(RSTStateMachine([], None))
    state.build_table = Mock()
    state.document = new_document("<rst-doc>", None)
    return CappaDirective(
        "cappa",
        [f"tests.ext.test_docutils.{cls_name}"],
        {"style": style, "terminal-width": terminal_width},
        [],  # type: ignore
        0,
        0,
        "",
        state,
        Mock(),
    )


def render(nodes):
    doc = new_document("<rst-doc>", None)
    doc += nodes
    return publish_from_doctree(doc, writer_name="html").decode()


def test_invalid():
    directive = create_directive(style="wat")
    with pytest.raises(ValueError):
        directive.run()


def test_terminal():
    directive = create_directive(style="terminal")
    nodes = directive.run()
    result = render(nodes)
    assert "Usage: foo" in result
    assert "BAR" in result
    assert "Show this message and exit." in result
    assert "asdf" in result


def test_native():
    directive = create_directive(style="native")
    nodes = directive.run()
    result = render(nodes)
    assert "<h1>foo</h1>" in result
    assert '<span class="section-subtitle">Arguments</span>' in result
    assert '<tt class="first docutils literal">bar BAR</tt>' in result
    assert '<span class="section-subtitle">Help</span>' in result
    assert (
        '<span class="pre">--help</span></tt><span>: Show this message and exit.</span>'
        in result
    )
    assert "asdf" in result


def test_has_help_desc():
    directive = create_directive(style="native", cls_name="Bar")
    nodes = directive.run()
    result = render(nodes)
    assert "has help" in result
    assert "has description" in result


def test_subcommand():
    directive = create_directive(style="native", cls_name="Subcommand")
    nodes = directive.run()
    result = render(nodes)
    assert "subcommand" in result


def test_terminal_width():
    directive = create_directive(style="terminal", terminal_width=60)
    nodes = directive.run()
    render(nodes)
