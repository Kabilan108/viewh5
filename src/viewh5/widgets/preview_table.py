from __future__ import annotations

from dataclasses import dataclass

from textual.binding import Binding
from textual.message import Message
from textual.widgets import DataTable

from viewh5.types import PreviewPage


class PreviewTable(DataTable[str]):
    BINDINGS = [
        Binding("k,up", "cursor_up", "Up", show=False),
        Binding("j,down", "cursor_down", "Down", show=False),
        Binding("ctrl+d,pagedown", "next_row_page", "Next page", show=False),
        Binding("ctrl+u,pageup", "previous_row_page", "Previous page", show=False),
        Binding("g", "first_row_page", "First page", show=False),
        Binding("G", "last_row_page", "Last page", show=False),
        Binding("[", "previous_column_page", "Previous columns", show=False),
        Binding("]", "next_column_page", "Next columns", show=False),
        Binding("h,escape,left", "return_to_tree", "Return", show=False),
    ]

    @dataclass
    class RowPageRequested(Message):
        preview_table: "PreviewTable"
        delta: int

        @property
        def control(self) -> "PreviewTable":
            return self.preview_table

    @dataclass
    class ColumnPageRequested(Message):
        preview_table: "PreviewTable"
        delta: int

        @property
        def control(self) -> "PreviewTable":
            return self.preview_table

    @dataclass
    class AbsoluteRowPageRequested(Message):
        preview_table: "PreviewTable"
        mode: str

        @property
        def control(self) -> "PreviewTable":
            return self.preview_table

    @dataclass
    class ReturnToTreeRequested(Message):
        preview_table: "PreviewTable"

        @property
        def control(self) -> "PreviewTable":
            return self.preview_table

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            zebra_stripes=True,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.cursor_type = "row"
        self.current_page: PreviewPage | None = None

    def show_page(self, page: PreviewPage) -> None:
        self.current_page = page
        self.clear(columns=True)
        self.fixed_columns = 1 if page.kind in {"table_1d", "table_2d"} else 0
        for column in page.columns:
            self.add_column(column)
        for row in page.rows:
            self.add_row(*row)
        if page.rows:
            self.move_cursor(row=0, column=0, animate=False)

    def action_next_row_page(self) -> None:
        self.post_message(self.RowPageRequested(self, 1))

    def action_previous_row_page(self) -> None:
        self.post_message(self.RowPageRequested(self, -1))

    def action_first_row_page(self) -> None:
        self.post_message(self.AbsoluteRowPageRequested(self, "first"))

    def action_last_row_page(self) -> None:
        self.post_message(self.AbsoluteRowPageRequested(self, "last"))

    def action_previous_column_page(self) -> None:
        self.post_message(self.ColumnPageRequested(self, -1))

    def action_next_column_page(self) -> None:
        self.post_message(self.ColumnPageRequested(self, 1))

    def action_return_to_tree(self) -> None:
        self.post_message(self.ReturnToTreeRequested(self))
