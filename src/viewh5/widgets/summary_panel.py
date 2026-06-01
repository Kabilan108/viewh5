from __future__ import annotations

from rich.console import Group
from rich.text import Text
from textual.widgets import Static

from viewh5.types import H5ObjectSummary

DEFAULT_VISIBLE_ATTRS = 1
DEFAULT_SUMMARY_HEIGHT = 15
MAX_SUMMARY_HEIGHT = 24
SUMMARY_VERTICAL_CHROME = 4


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

    def show_summary(
        self,
        summary: H5ObjectSummary,
        *,
        show_all_attrs: bool = False,
        visible_attr_count: int = DEFAULT_VISIBLE_ATTRS,
    ) -> None:
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
            visible_attrs = summary.attrs if show_all_attrs else summary.attrs[:visible_attr_count]
            for key, value in visible_attrs:
                rows.append(self._line(key, value))
            hidden_count = len(summary.attrs) - len(visible_attrs)
            if hidden_count > 0:
                rows.append(Text(f"  ... {hidden_count} more attribute(s); press a to show all", style="dim"))
            elif show_all_attrs and len(summary.attrs) > visible_attr_count:
                rows.append(Text("  showing all attributes; press a to collapse", style="dim"))
        else:
            rows.append(Text("  none", style="dim"))
        if show_all_attrs and len(summary.attrs) > visible_attr_count:
            self.styles.height = min(max(DEFAULT_SUMMARY_HEIGHT, len(rows) + SUMMARY_VERTICAL_CHROME), MAX_SUMMARY_HEIGHT)
        else:
            self.styles.height = DEFAULT_SUMMARY_HEIGHT
        self.update(Group(*rows))

    def _line(self, key: str, value: str) -> Text:
        text = Text()
        text.append(f"{key}: ", style="bold")
        text.append(value)
        return text
