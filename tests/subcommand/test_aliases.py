from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Union

import pytest

import cappa
from tests.utils import Backend, backends, parse, parse_completion


@cappa.command(aliases=["ls"])
@dataclass
class List:
    pass


@cappa.command(
    aliases=[cappa.Alias("rm", deprecated="use remove")],
)
@dataclass
class Remove:
    pass


@dataclass
class Tool:
    cmd: cappa.Subcommands[Union[List, Remove]]


@backends
def test_visible_alias_dispatches(backend: Backend):
    result = parse(Tool, "list", backend=backend)
    assert isinstance(result.cmd, List)

    result = parse(Tool, "ls", backend=backend)
    assert isinstance(result.cmd, List)


@backends
def test_canonical_still_dispatches(backend: Backend):
    result = parse(Tool, "remove", backend=backend)
    assert isinstance(result.cmd, Remove)


@backends
def test_deprecated_alias_warns(backend: Backend, capsys: Any):
    result = parse(Tool, "rm", backend=backend)
    assert isinstance(result.cmd, Remove)

    err = capsys.readouterr().err
    assert "Command alias `rm` is deprecated: use remove" in err


@backends
def test_canonical_does_not_warn(backend: Backend, capsys: Any):
    parse(Tool, "remove", backend=backend)
    err = capsys.readouterr().err
    assert "deprecated" not in err


@cappa.command(aliases=[cappa.Alias("del", deprecated=True)])
@dataclass
class DeleteBool:
    pass


@dataclass
class DeleteBoolRoot:
    cmd: cappa.Subcommands[DeleteBool]


@backends
def test_deprecated_alias_bool_warns_without_suffix(backend: Backend, capsys: Any):
    """`deprecated=True` (bool) emits the default message with no `:` suffix."""
    result = parse(DeleteBoolRoot, "del", backend=backend)
    assert isinstance(result.cmd, DeleteBool)

    err = capsys.readouterr().err
    assert "Command alias `del` is deprecated" in err
    assert "Command alias `del` is deprecated:" not in err


# --- Hidden alias ---


@cappa.command(aliases=[cappa.Alias("dir", hidden=True)])
@dataclass
class HiddenList:
    pass


@dataclass
class HiddenTool:
    cmd: cappa.Subcommands[HiddenList]


@backends
def test_hidden_alias_dispatches(backend: Backend):
    result = parse(HiddenTool, "dir", backend=backend)
    assert isinstance(result.cmd, HiddenList)


@backends
def test_hidden_alias_not_in_help(backend: Backend, capsys: Any):
    with pytest.raises(cappa.Exit):
        parse(HiddenTool, "--help", backend=backend)

    out = capsys.readouterr().out
    assert "dir" not in out
    assert "hidden-list" in out


# --- Completion ---


def test_completion_includes_visible_alias():
    result = parse_completion(Tool, "")
    assert result is not None
    assert "list" in result
    assert "ls" in result
    assert "remove" in result
    assert "rm" in result


def test_completion_excludes_hidden_alias():
    result = parse_completion(HiddenTool, "")
    assert result is not None
    assert "hidden-list" in result
    assert "dir" not in result


# --- Help rendering ---


@backends
def test_visible_aliases_in_help(backend: Backend, capsys: Any):
    with pytest.raises(cappa.Exit):
        parse(Tool, "--help", backend=backend)

    out = capsys.readouterr().out
    assert "list, ls" in out
    assert "remove, rm (deprecated)" in out


# --- Imperative construction ---


@dataclass
class ImpA:
    pass


@dataclass
class ImpB:
    pass


@backends
def test_imperative_aliases(backend: Backend):
    """Aliases declared on Command directly (not via decorator) work the same way."""
    sub = cappa.Subcommand(
        field_name="cmd",
        options={
            "imp-a": cappa.Command(ImpA, name="imp-a", aliases=["a"]),
            "imp-b": cappa.Command(ImpB, name="imp-b", aliases=["b"]),
        },
    )

    @dataclass
    class ImpRoot:
        cmd: cappa.Subcommands[Union[ImpA, ImpB]]

    cmd = cappa.Command(ImpRoot, arguments=[sub])
    result = parse(cmd, "a", backend=backend)
    assert isinstance(result.cmd, ImpA)

    result = parse(cmd, "b", backend=backend)
    assert isinstance(result.cmd, ImpB)


# --- Collisions ---


@cappa.command(aliases=["self-collide"])
@dataclass
class SelfCollide:
    pass


@dataclass
class SelfCollideRoot:
    cmd: cappa.Subcommands[SelfCollide]


def test_alias_collides_with_own_canonical_name():
    with pytest.raises(ValueError, match="matching its own name"):
        cappa.collect(SelfCollideRoot)


@cappa.command(name="collide-x")
@dataclass
class CollideX:
    pass


@cappa.command(aliases=["collide-x"])
@dataclass
class CollideY:
    pass


@dataclass
class CollideXYRoot:
    cmd: cappa.Subcommands[Union[CollideX, CollideY]]


def test_alias_collides_with_other_canonical_name():
    with pytest.raises(ValueError, match="collides with another subcommand"):
        cappa.collect(CollideXYRoot)


@cappa.command(aliases=["shared"])
@dataclass
class CollideA:
    pass


@cappa.command(aliases=["shared"])
@dataclass
class CollideB:
    pass


@dataclass
class CollideABRoot:
    cmd: cappa.Subcommands[Union[CollideA, CollideB]]


def test_alias_collides_with_other_alias():
    with pytest.raises(ValueError, match="declared on both"):
        cappa.collect(CollideABRoot)


# --- Defensive helpers (direct unit calls) ---


def test_visible_aliases_for_unknown_canonical_returns_empty():
    """`visible_aliases_for` returns [] when given a name that isn't a subcommand."""
    sub = cappa.Subcommand(field_name="cmd", options={})
    assert sub.visible_aliases_for("not-a-subcommand") == []


def test_warn_deprecated_alias_no_op_for_unknown_name(capsys: Any):
    """`_warn_deprecated_alias` is a no-op when the typed name isn't an alias."""
    from cappa.output import Output

    sub = cappa.Subcommand(field_name="cmd", options={})
    sub._warn_deprecated_alias(Output(), "ghost-alias")
    err = capsys.readouterr().err
    assert err == ""


def test_format_subcommand_without_subcommand_arg():
    """`format_subcommand` works with the default `subcommand=None`."""
    from cappa.help import HelpFormatter, format_subcommand

    cmd = cappa.Command(List)
    padding, help_text = format_subcommand(HelpFormatter(), cmd)
    rendered = str(padding.renderable)
    assert "list" in rendered
    assert "ls" not in rendered  # aliases only appear when subcommand is provided
    assert help_text == cmd.help
