from __future__ import annotations

from dataclasses import dataclass
from typing import Generator

from textual.binding import Binding
from textual.widgets import Tree
from textual.widgets.tree import TreeNode


@dataclass(slots=True)
class TreeEntry:
    path: str
    kind: str
    loaded: bool = False


class ObjectTree(Tree[TreeEntry]):
    DEFAULT_CSS = """
    ObjectTree {
        scrollbar-size-horizontal: 0;
    }
    """

    BINDINGS = [
        Binding("k,up", "cursor_up", "Up", show=False),
        Binding("j,down", "cursor_down", "Down", show=False),
        Binding("g", "scroll_home", "Top", show=False),
        Binding("G", "scroll_end", "Bottom", show=False),
        Binding("h,left", "collapse_or_parent", "Collapse", show=False),
        Binding("l,right,enter", "activate_node", "Open", show=False),
        Binding("space", "toggle_node", "Toggle", show=False),
        Binding("J", "next_expandable", "Next expandable", show=False),
        Binding("K", "previous_expandable", "Previous expandable", show=False),
    ]

    def action_collapse_or_parent(self) -> None:
        node = self.cursor_node
        if node is None:
            return
        if node.allow_expand and node.is_expanded:
            node.collapse()
            return
        if node.parent is not None:
            self.move_cursor(node.parent, animate=False)

    def action_activate_node(self) -> None:
        node = self.cursor_node
        if node is None:
            return
        if node.allow_expand and node.is_collapsed:
            node.expand()
            return
        self.post_message(Tree.NodeSelected(node))

    def action_next_expandable(self) -> None:
        self._jump_expandable(step=1)

    def action_previous_expandable(self) -> None:
        self._jump_expandable(step=-1)

    def walk_nodes(self) -> Generator[TreeNode[TreeEntry], None, None]:
        for node in self._tree_nodes.values():
            yield node

    def _jump_expandable(self, step: int) -> None:
        if self.cursor_line < 0:
            return
        max_line = len(self._tree_lines)
        current = self.cursor_line + step
        while 0 <= current < max_line:
            node = self.get_node_at_line(current)
            if node is not None and node.allow_expand:
                self.cursor_line = current
                self.scroll_to_line(current, animate=False)
                return
            current += step
