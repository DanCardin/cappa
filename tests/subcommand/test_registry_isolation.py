from __future__ import annotations

from typing import Any

import pytest

import cappa
from cappa.command import FinalCommand
from tests.utils import Backend, backends


@pytest.fixture(params=[False, True], ids=["default", "custom"])
def registry(request: pytest.FixtureRequest) -> cappa.Registry:
    return cappa.Registry() if request.param else cappa.default_registry


def make_command(use_first: bool, registry: cappa.Registry) -> type:
    @cappa.command(registry=registry)
    class Root:
        if use_first:

            @cappa.command(help="First application only", registry=registry)
            def first(self) -> None:
                pass

        else:

            @cappa.command(help="Second application only", registry=registry)
            def second(self) -> None:
                pass

    return Root


@backends
def test_factory_commands_stay_separate(
    backend: Backend, registry: cappa.Registry, capsys: Any
):
    first = make_command(True, registry)
    first_command: FinalCommand[Any] = cappa.collect(first, registry=registry)
    assert first_command.subcommand is not None
    assert list(first_command.subcommand.options) == ["first"]

    second = make_command(False, registry)
    for cls, own_name, other_name in (
        (first, "first", "second"),
        (second, "second", "first"),
        (make_command(True, registry), "first", "second"),
    ):
        command: FinalCommand[Any] = cappa.collect(cls, registry=registry)
        assert command.subcommand is not None
        assert list(command.subcommand.options) == [own_name]
        assert isinstance(
            cappa.parse(cls, argv=[own_name], backend=backend, registry=registry), cls
        )
        with pytest.raises(cappa.Exit):
            cappa.parse(cls, argv=[other_name], backend=backend, registry=registry)
        capsys.readouterr()
        with pytest.raises(cappa.Exit):
            cappa.parse(cls, argv=["--help"], backend=backend, registry=registry)
        help_text = capsys.readouterr().out
        assert own_name in help_text
        assert other_name not in help_text


@backends
def test_same_named_static_commands_invoke_their_own_function(
    backend: Backend, registry: cappa.Registry
):
    def factory(value: str) -> type:
        @cappa.command(registry=registry)
        class Root:
            @staticmethod
            @cappa.command(registry=registry)
            def show() -> str:
                return value

        return Root

    first = factory("first")
    second = factory("second")
    for cls, expected in ((first, "first"), (second, "second"), (first, "first")):
        assert (
            cappa.invoke(cls, argv=["show"], backend=backend, registry=registry)
            == expected
        )


@backends
def test_descriptor_and_alias_members(backend: Backend, registry: cappa.Registry):
    @cappa.command(registry=registry)
    class Root:
        @staticmethod
        @cappa.command(registry=registry)
        def static(value: int) -> int:
            return value

        @classmethod
        @cappa.command(registry=registry)
        def class_method(cls, value: int) -> int:
            return value

        @cappa.command(registry=registry)
        def original(self) -> None:
            pass

        alias = original
        del original

    command = cappa.collect(Root, registry=registry)
    assert command.subcommand is not None
    assert list(command.subcommand.options) == ["static", "class-method", "original"]
    for argv in (["static", "1"], ["class-method", "1"], ["original"]):
        assert isinstance(
            cappa.parse(Root, argv=argv, backend=backend, registry=registry), Root
        )


@backends
def test_subclasses_keep_their_own_method_declarations(
    backend: Backend, registry: cappa.Registry
):
    @cappa.command(registry=registry)
    class Parent:
        @cappa.command(help="Parent implementation", registry=registry)
        def action(self) -> None:
            pass

    @cappa.command(registry=registry)
    class Child(Parent):
        @cappa.command(help="Child implementation", registry=registry)
        def action(self) -> None:
            pass

    parent_command = cappa.collect(Parent, registry=registry)
    child_command = cappa.collect(Child, registry=registry)
    assert parent_command.subcommand is not None
    assert child_command.subcommand is not None
    assert parent_command.subcommand.options["action"].help == "Parent implementation"
    assert child_command.subcommand.options["action"].help == "Child implementation"
    assert isinstance(
        cappa.parse(Child, argv=["action"], backend=backend, registry=registry), Child
    )
