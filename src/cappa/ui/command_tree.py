from __future__ import annotations

from typing import ClassVar

from rich.style import Style
from rich.text import Text, TextType
from textual.widgets import Tree
from textual.widgets._tree import TreeDataType, TreeNode

import cappa


class CommandTree(Tree[cappa.Command]):
    COMPONENT_CLASSES: ClassVar[set[str]] = {"group"}

    def __init__(self, label: TextType, command: cappa.Command):
        super().__init__(label, command)
        self.show_root = False
        self.guide_depth = 2
        self.show_guides = False
        self.command = command
        self.command_name = command.real_name()

    def render_label(
        self, node: TreeNode[TreeDataType], base_style: Style, style: Style
    ) -> Text:
        label = node._label.copy()
        label.stylize(style)
        return label

    def on_mount(self):
        def build_tree(node: TreeNode, command: cappa.Command):
            node.add_leaf(command.real_name(), data=command)
            # subcommand = command.subcommand
            # for arg in command.arguments:
            #     if arg is subcommand:
            #         continue
            #
            #     node.add_leaf(assert_type(arg.field_name, str), data=arg)
            #
            # if subcommand:
            #     label = Text(assert_type(subcommand.field_name, str))
            #
            #     group_style = self.get_component_rich_style("group")
            #     label.stylize(group_style)
            #     label.append(" ")
            #     label.append("group", "dim i")
            #
            #     for subcommand in subcommand.options.values():
            #         child = node.add(label, allow_expand=False, data=subcommand)
            #         build_tree(subcommand, child)

        build_tree(self.root, self.command)
        # raise Exception(self.root)
        self.root.expand_all()
        self.select_node(self.root)

        super().on_mount()
