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
            if command.subcommand:
                branch = node.add(command.real_name(), data=command, expand=True)
                for sub_cmd in command.subcommand.options.values():
                    build_tree(branch, sub_cmd)
            else:
                node.add_leaf(command.real_name(), data=command)

        def first_leaf(node: TreeNode) -> TreeNode:
            return node if not node.children else first_leaf(node.children[0])

        super().on_mount()
        build_tree(self.root, self.command)

        start = self.root.children[0] if self.root.children else self.root
        self.call_after_refresh(self.select_node, first_leaf(start))
