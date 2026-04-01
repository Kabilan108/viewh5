from __future__ import annotations

import asyncio
from math import ceil
from pathlib import PurePosixPath

from rich.text import Text
from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Static
from textual.widgets.tree import TreeNode

from viewh5.model import COLUMN_PAGE_SIZE_2D, HDF5Model, ROW_PAGE_SIZE_1D, ROW_PAGE_SIZE_2D
from viewh5.types import H5ChildEntry, H5ObjectSummary, PreviewPage, SearchHit
from viewh5.widgets.object_tree import ObjectTree, TreeEntry
from viewh5.widgets.preview_table import PreviewTable
from viewh5.widgets.search_modal import SearchModal
from viewh5.widgets.summary_panel import SummaryPanel


class MainScreen(Screen[None]):
    BINDINGS = [
        Binding("/", "open_search", "Search", show=True),
        Binding("r", "reload_file", "Reload", show=True),
        Binding("p", "force_preview", "Preview", show=True),
    ]

    CSS = """
    MainScreen {
        layout: vertical;
    }

    #status-bar {
        height: 1;
        background: $boost;
        color: $text;
        padding: 0 1;
    }

    #content {
        height: 1fr;
    }

    #object-tree {
        width: 34;
        border: round $border;
    }

    #right-pane {
        width: 1fr;
    }

    #preview-message {
        min-height: 3;
        border: round $border;
        padding: 1 2;
        margin-top: 1;
    }

    #preview-table {
        height: 1fr;
        margin-top: 1;
        border: round $border;
    }
    """

    def __init__(self, model: HDF5Model) -> None:
        super().__init__()
        self.model = model
        self.current_path = "/"
        self.current_summary: H5ObjectSummary | None = None
        self.current_preview: PreviewPage | None = None
        self.path_to_node: dict[str, TreeNode[TreeEntry]] = {}
        self.search_hits: list[SearchHit] | None = None
        self.preview_force = False
        self.selected_row_offset = 0
        self.selected_column_offset = 0

    def compose(self) -> ComposeResult:
        yield Static(id="status-bar")
        with Horizontal(id="content"):
            yield ObjectTree("/", data=TreeEntry("/", "file", loaded=False), id="object-tree")
            with Vertical(id="right-pane"):
                yield SummaryPanel(id="summary-panel")
                yield Static("Select a dataset to preview values.", id="preview-message")
                yield PreviewTable(id="preview-table")
        yield Footer()

    def on_mount(self) -> None:
        self.tree.focus()
        self._set_status("Loading root metadata")
        self.load_root()

    @property
    def tree(self) -> ObjectTree:
        return self.query_one(ObjectTree)

    @property
    def summary_panel(self) -> SummaryPanel:
        return self.query_one(SummaryPanel)

    @property
    def preview_message(self) -> Static:
        return self.query_one("#preview-message", Static)

    @property
    def preview_table(self) -> PreviewTable:
        return self.query_one(PreviewTable)

    @work(exclusive=True, group="root")
    async def load_root(self, restore_path: str = "/") -> None:
        try:
            root_summary, root_children = await asyncio.gather(
                asyncio.to_thread(self.model.get_root_summary),
                asyncio.to_thread(self.model.list_children, "/"),
            )
        except Exception as error:
            self.preview_message.update(str(error))
            self._set_status(f"Failed to load {self.model.path}")
            return

        self.tree.reset("/", TreeEntry("/", "file", loaded=True))
        self.tree.root.expand()
        self.path_to_node = {"/": self.tree.root}
        self._populate_children(self.tree.root, root_children)
        self.current_path = "/"
        self.selected_row_offset = 0
        self.selected_column_offset = 0
        self.preview_force = False
        self._apply_summary(root_summary)
        self._apply_preview(
            PreviewPage(
                path="/",
                kind="unsupported",
                columns=[],
                rows=[],
                row_offset=0,
                total_rows=0,
                column_offset=0,
                total_columns=0,
                warning="Preview is only available for datasets.",
            )
        )
        self.tree.move_cursor(self.tree.root, animate=False)
        if restore_path != "/":
            await self.reveal_path(restore_path)
        self._set_status_for_state()

    @work(exclusive=False, group="children")
    async def load_children(self, path: str) -> None:
        node = self.path_to_node.get(path)
        if node is None or node.data is None or node.data.loaded:
            return
        children = await asyncio.to_thread(self.model.list_children, path)
        node.data.loaded = True
        self._populate_children(node, children)

    @work(exclusive=True, group="selection")
    async def load_selection(
        self,
        path: str,
        *,
        focus_preview: bool = False,
        force_preview: bool = False,
        row_offset: int = 0,
        column_offset: int = 0,
    ) -> None:
        self.current_path = path
        self.preview_force = force_preview
        self.selected_row_offset = row_offset
        self.selected_column_offset = column_offset

        try:
            summary = await asyncio.to_thread(self.model.get_summary, path)
        except Exception as error:
            self.preview_message.update(str(error))
            self._set_status(f"Failed to load {path}")
            return

        if self.current_path != path:
            return

        self._apply_summary(summary)
        if summary.kind != "dataset":
            preview = PreviewPage(
                path=path,
                kind="unsupported",
                columns=[],
                rows=[],
                row_offset=0,
                total_rows=0,
                column_offset=0,
                total_columns=0,
                warning="Preview is only available for datasets.",
            )
            self._apply_preview(preview)
            self._set_status_for_state()
            return

        self.preview_message.update("Loading preview...")
        preview = await asyncio.to_thread(
            self.model.get_preview,
            path,
            row_offset,
            column_offset,
            force_preview,
        )
        if self.current_path != path:
            return
        self._apply_preview(preview)
        self._set_status_for_state()
        if focus_preview and preview.kind not in {"unsupported", "blocked"}:
            self.preview_table.focus()

    @work(exclusive=True, group="search")
    async def open_search_modal_worker(self) -> None:
        self._set_status("Building search index")
        if self.search_hits is None:
            self.search_hits = await asyncio.to_thread(self.model.build_search_index)
        hit = await self.app.push_screen_wait(SearchModal(self.search_hits))
        if hit is None:
            self._set_status_for_state()
            return
        await self.reveal_path(hit.path)
        self.tree.focus()

    @on(ObjectTree.NodeExpanded, "#object-tree")
    def on_tree_expanded(self, event: ObjectTree.NodeExpanded[TreeEntry]) -> None:
        entry = event.node.data
        if entry is None or entry.kind == "dataset" or entry.loaded:
            return
        self.load_children(entry.path)

    @on(ObjectTree.NodeHighlighted, "#object-tree")
    def on_tree_highlighted(self, event: ObjectTree.NodeHighlighted[TreeEntry]) -> None:
        entry = event.node.data
        if entry is None:
            return
        self.preview_force = False
        self.selected_row_offset = 0
        self.selected_column_offset = 0
        self.load_selection(entry.path)

    @on(ObjectTree.NodeSelected, "#object-tree")
    def on_tree_selected(self, event: ObjectTree.NodeSelected[TreeEntry]) -> None:
        entry = event.node.data
        if entry is None:
            return
        focus_preview = entry.kind == "dataset"
        self.preview_force = False
        self.selected_row_offset = 0
        self.selected_column_offset = 0
        self.load_selection(entry.path, focus_preview=focus_preview)

    @on(PreviewTable.RowPageRequested, "#preview-table")
    def on_row_page_requested(self, event: PreviewTable.RowPageRequested) -> None:
        if self.current_summary is None or self.current_summary.kind != "dataset" or self.current_preview is None:
            return
        page_size = ROW_PAGE_SIZE_1D if self.current_preview.kind == "table_1d" else ROW_PAGE_SIZE_2D
        next_offset = self.current_preview.row_offset + (event.delta * page_size)
        self.load_selection(
            self.current_path,
            force_preview=self.preview_force,
            row_offset=next_offset,
            column_offset=self.current_preview.column_offset,
        )

    @on(PreviewTable.ColumnPageRequested, "#preview-table")
    def on_column_page_requested(self, event: PreviewTable.ColumnPageRequested) -> None:
        if self.current_summary is None or self.current_summary.kind != "dataset" or self.current_preview is None:
            return
        if self.current_preview.kind != "table_2d":
            return
        next_offset = self.current_preview.column_offset + (event.delta * COLUMN_PAGE_SIZE_2D)
        self.load_selection(
            self.current_path,
            force_preview=self.preview_force,
            row_offset=self.current_preview.row_offset,
            column_offset=next_offset,
        )

    @on(PreviewTable.AbsoluteRowPageRequested, "#preview-table")
    def on_absolute_row_page_requested(self, event: PreviewTable.AbsoluteRowPageRequested) -> None:
        if self.current_summary is None or self.current_summary.kind != "dataset" or self.current_preview is None:
            return
        if event.mode == "first":
            offset = 0
        else:
            page_size = ROW_PAGE_SIZE_1D if self.current_preview.kind == "table_1d" else ROW_PAGE_SIZE_2D
            pages = max(ceil(self.current_preview.total_rows / page_size) - 1, 0)
            offset = pages * page_size
        self.load_selection(
            self.current_path,
            force_preview=self.preview_force,
            row_offset=offset,
            column_offset=self.current_preview.column_offset,
        )

    @on(PreviewTable.ReturnToTreeRequested, "#preview-table")
    def on_return_to_tree_requested(self) -> None:
        self.tree.focus()

    def action_open_search(self) -> None:
        self.open_search_modal_worker()

    def action_reload_file(self) -> None:
        self.load_root(restore_path=self.current_path)

    def action_force_preview(self) -> None:
        if self.current_summary is None or self.current_summary.kind != "dataset":
            return
        self.preview_force = True
        self.load_selection(
            self.current_path,
            focus_preview=True,
            force_preview=True,
            row_offset=self.selected_row_offset,
            column_offset=self.selected_column_offset,
        )

    async def reveal_path(self, path: str) -> None:
        if path == "/":
            self.tree.move_cursor(self.tree.root, animate=False)
            self.tree.focus()
            return

        current = self.tree.root
        for candidate in self._ancestor_chain(path):
            current_entry = current.data
            if current_entry is not None and not current_entry.loaded and current_entry.kind != "dataset":
                children = await asyncio.to_thread(self.model.list_children, current_entry.path)
                current_entry.loaded = True
                self._populate_children(current, children)
            if current.is_collapsed:
                current.expand()
            current = self.path_to_node[candidate]

        self.tree.move_cursor(current, animate=False)
        self.tree.focus()
        self.preview_force = False
        self.selected_row_offset = 0
        self.selected_column_offset = 0
        self.load_selection(path)

    def _populate_children(self, node: TreeNode[TreeEntry], children: list[H5ChildEntry]) -> None:
        existing_paths = {
            child.data.path
            for child in node.children
            if child.data is not None
        }
        for child in children:
            if child.path in existing_paths:
                continue
            label = child.name + ("/" if child.kind == "group" else "")
            new_node = node.add(
                label,
                data=TreeEntry(child.path, child.kind, loaded=False),
                expand=False,
                allow_expand=child.expandable,
            )
            self.path_to_node[child.path] = new_node

    def _apply_summary(self, summary: H5ObjectSummary) -> None:
        self.current_summary = summary
        self.summary_panel.show_summary(summary)

    def _apply_preview(self, preview: PreviewPage) -> None:
        self.current_preview = preview
        self.selected_row_offset = preview.row_offset
        self.selected_column_offset = preview.column_offset
        self.preview_table.show_page(preview)
        if preview.warning:
            self.preview_message.update(preview.warning)
        elif preview.kind in {"scalar", "table_1d", "table_2d"}:
            self.preview_message.update(self._preview_window_text(preview))
        else:
            self.preview_message.update("No preview available.")

    def _preview_window_text(self, preview: PreviewPage) -> str:
        if preview.kind == "scalar":
            return "Scalar dataset preview."
        if preview.kind == "table_1d":
            start = preview.row_offset
            stop = start + len(preview.rows)
            return f"Rows {start}-{max(stop - 1, start)} of {preview.total_rows}"
        start_row = preview.row_offset
        stop_row = start_row + len(preview.rows)
        start_column = preview.column_offset
        visible_columns = max(len(preview.columns) - 1, 0)
        stop_column = start_column + visible_columns
        return (
            f"Rows {start_row}-{max(stop_row - 1, start_row)} of {preview.total_rows}; "
            f"columns {start_column}-{max(stop_column - 1, start_column)} of {preview.total_columns}"
        )

    def _set_status(self, message: str) -> None:
        self.query_one("#status-bar", Static).update(message)

    def _set_status_for_state(self) -> None:
        summary = self.current_summary
        preview = self.current_preview
        if summary is None:
            self._set_status(str(self.model.path))
            return
        text = Text()
        text.append(str(self.model.path), style="bold")
        text.append(" | ")
        text.append(summary.path, style="cyan")
        text.append(" | ")
        text.append(summary.kind)
        if summary.dtype is not None:
            text.append(" | ")
            text.append(summary.dtype)
        if summary.shape is not None:
            text.append(" ")
            text.append(str(summary.shape), style="magenta")
        if preview is not None:
            text.append(" | ")
            if preview.kind in {"scalar", "table_1d", "table_2d"}:
                text.append("preview ready", style="green")
            elif preview.kind == "blocked":
                text.append("preview gated", style="yellow")
            else:
                text.append("metadata only", style="dim")
        self.query_one("#status-bar", Static).update(text)

    def _ancestor_chain(self, path: str) -> list[str]:
        current = PurePosixPath(path)
        ancestors = []
        parts = current.parts[1:]
        built = ""
        for part in parts:
            built = f"{built}/{part}"
            ancestors.append(built)
        return ancestors
