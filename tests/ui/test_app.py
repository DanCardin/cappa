from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Literal, Union

from typing_extensions import Annotated

import cappa
from cappa.ui.base import CLIApp, CommandBuilder
from cappa.ui.command_tree import CommandTree
from cappa.ui.form import CommandForm
from cappa.ui.parameter_controls import ParameterControls


@dataclass
class FlatCmd:
    """A flat command with no subcommands."""

    name: str
    flag: bool = False
    level: Annotated[Literal["low", "high"], cappa.Arg(long=True)] = "low"


@dataclass
class Sub1:
    value: int = 0


@dataclass
class Sub2:
    label: str = ""


@cappa.command(name="root")
@dataclass
class SubCmd:
    """Command with subcommands."""

    sub: Annotated[Union[Sub1, Sub2], cappa.Subcommand()]


async def settle(pilot, n: int = 3):
    for _ in range(n):
        await pilot.pause()


def run_app(coro):
    return asyncio.run(coro)


def test_flat_command_mounts_form():
    async def run():
        async with CLIApp(FlatCmd).run_test() as pilot:
            await settle(pilot)
            form = pilot.app.query_one(CommandForm)
            controls = list(form.query(ParameterControls))
            field_names = {c.arg.field_name for c in controls}
            assert field_names == {"name", "flag", "level"}

    run_app(run())


def test_flat_command_command_data_set_on_mount():
    async def run():
        async with CLIApp(FlatCmd).run_test() as pilot:
            await settle(pilot)
            builder = pilot.app.query_one(CommandBuilder)
            assert builder.command_data is not None

    run_app(run())


def test_subcommand_tree_shows_leaves():
    async def run():
        async with CLIApp(SubCmd).run_test() as pilot:
            await settle(pilot)
            tree = pilot.app.query_one(CommandTree)
            root_branch = tree.root.children[0]
            leaf_labels = {str(node.label) for node in root_branch.children}
            assert "sub1" in leaf_labels
            assert "sub2" in leaf_labels

    run_app(run())


def test_subcommand_tree_navigation_updates_form():
    async def run():
        async with CLIApp(SubCmd).run_test() as pilot:
            await settle(pilot)
            tree = pilot.app.query_one(CommandTree)
            root_branch = tree.root.children[0]
            sub2_node = root_branch.children[1]
            tree.select_node(sub2_node)
            await settle(pilot)
            form = pilot.app.query_one(CommandForm)
            assert form.command.real_name() == "sub2"

    run_app(run())
