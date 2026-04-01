from __future__ import annotations

from rich.console import Group
from rich.text import Text
from textual.widgets import Static

from viewh5.types import H5ObjectSummary


class SummaryPanel(Static):
    DEFAULT_CSS = """
    SummaryPanel {
        height: 15;
        min-height: 10;
        border: round $border;
        padding: 1 2;
        overflow-y: auto;
    }
    """

    def show_summary(self, summary: H5ObjectSummary) -> None:
        rows = [
            self._line("Path", summary.path),
            self._line("Kind", summary.kind),
        ]
        if summary.dtype is not None:
            rows.append(self._line("Dtype", summary.dtype))
        if summary.shape is not None:
            rows.append(self._line("Shape", str(summary.shape)))
        if summary.nbytes is not None:
            rows.append(self._line("Bytes", f"{summary.nbytes:,}"))
        if summary.chunks is not None:
            rows.append(self._line("Chunks", str(summary.chunks)))
        if summary.compression is not None:
            rows.append(self._line("Compression", summary.compression))
        if summary.child_count is not None:
            rows.append(self._line("Children", str(summary.child_count)))
        rows.append(self._line("Preview", summary.preview_risk))
        if summary.preview_reason:
            rows.append(self._line("Reason", summary.preview_reason))
        rows.append(Text(""))
        rows.append(Text("Attributes", style="bold"))
        if summary.attrs:
            for key, value in summary.attrs:
                rows.append(self._line(key, value))
        else:
            rows.append(Text("  none", style="dim"))
        self.update(Group(*rows))

    def _line(self, key: str, value: str) -> Text:
        text = Text()
        text.append(f"{key}: ", style="bold")
        text.append(value)
        return text
