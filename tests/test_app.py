from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import h5py
import pytest

from viewh5.app import HDF5ViewerApp
from viewh5.screens.main import MainScreen
from viewh5.types import PreviewPage
from viewh5.widgets.object_tree import ObjectTree
from viewh5.widgets.preview_table import PreviewTable
from viewh5.widgets.summary_panel import DEFAULT_SUMMARY_HEIGHT, SummaryPanel
from textual.widgets import Static


@pytest.mark.asyncio
async def test_startup_focuses_tree(sample_hdf5_file: Path) -> None:
    async with HDF5ViewerApp(sample_hdf5_file).run_test() as pilot:
        await pilot.pause()
        tree = pilot.app.screen.query_one(ObjectTree)
        assert pilot.app.screen.focused is tree


@pytest.mark.asyncio
async def test_tree_navigation_and_preview(sample_hdf5_file: Path) -> None:
    async with HDF5ViewerApp(sample_hdf5_file).run_test() as pilot:
        await pilot.pause()
        await pilot.press("j")
        await pilot.pause()
        await pilot.press("l")
        await pilot.pause()
        await pilot.press("j")
        await pilot.pause()
        preview_message = pilot.app.screen.query_one("#preview-message", Static)
        assert "Rows" in str(preview_message.content)


@pytest.mark.asyncio
async def test_blocked_preview_does_not_auto_load(sample_hdf5_file: Path) -> None:
    async with HDF5ViewerApp(sample_hdf5_file).run_test() as pilot:
        await pilot.pause()
        await pilot.press("j", "j")
        await pilot.pause()
        preview_message = pilot.app.screen.query_one("#preview-message", Static)
        assert "Press p to load it" in str(preview_message.content)


@pytest.mark.asyncio
async def test_force_preview_can_be_monkeypatched_for_app_flow(
    sample_hdf5_file: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_get_preview = HDF5ViewerApp(sample_hdf5_file).model.get_preview

    def fake_get_preview(path: str, row_offset: int = 0, column_offset: int = 0, force: bool = False) -> PreviewPage:
        if path == "/blocked" and force:
            return PreviewPage(
                path=path,
                kind="table_1d",
                columns=["index", "value"],
                rows=[["0", "0.0"], ["1", "0.0"]],
                row_offset=0,
                total_rows=40_000_000,
                column_offset=0,
                total_columns=2,
                warning=None,
            )
        return original_get_preview(path, row_offset=row_offset, column_offset=column_offset, force=force)

    async with HDF5ViewerApp(sample_hdf5_file).run_test() as pilot:
        app = cast(HDF5ViewerApp, pilot.app)
        monkeypatch.setattr(app.model, "get_preview", fake_get_preview)
        await pilot.pause()
        await pilot.press("j", "j")
        await pilot.pause()
        await pilot.press("p")
        await pilot.pause()
        table = pilot.app.screen.query_one(PreviewTable)
        assert table.row_count == 2


@pytest.mark.asyncio
async def test_tab_moves_focus_to_preview(sample_hdf5_file: Path) -> None:
    async with HDF5ViewerApp(sample_hdf5_file).run_test() as pilot:
        await pilot.pause()
        await pilot.press("j", "l", "j")
        await pilot.pause()
        await pilot.press("tab")
        await pilot.pause()
        assert pilot.app.screen.focused is pilot.app.screen.query_one(PreviewTable)


@pytest.mark.asyncio
async def test_search_jumps_to_path(sample_hdf5_file: Path) -> None:
    async with HDF5ViewerApp(sample_hdf5_file).run_test() as pilot:
        await pilot.pause()
        await pilot.press("/")
        await pilot.pause()
        await pilot.press(*"vector")
        await pilot.press("enter")
        await pilot.pause()
        screen = cast(MainScreen, pilot.app.screen)
        assert screen.current_path == "/group/vector"


@pytest.mark.asyncio
async def test_attributes_are_truncated_with_toggle_hint(tmp_path: Path) -> None:
    path = _multi_attr_file(tmp_path)

    async with HDF5ViewerApp(path).run_test() as pilot:
        await pilot.pause()
        await pilot.press("j")
        await pilot.pause()
        panel = pilot.app.screen.query_one(SummaryPanel)
        content = _summary_text(panel)

        assert "alpha: one" in content
        assert "beta: two" not in content
        assert "... 4 more attribute(s); press a to show all" in content
        assert _panel_height(panel) == DEFAULT_SUMMARY_HEIGHT


@pytest.mark.asyncio
async def test_attribute_toggle_expands_full_list(tmp_path: Path) -> None:
    path = _multi_attr_file(tmp_path)

    async with HDF5ViewerApp(path).run_test() as pilot:
        await pilot.pause()
        await pilot.press("j")
        await pilot.pause()
        await pilot.press("a")
        await pilot.pause()
        panel = pilot.app.screen.query_one(SummaryPanel)
        content = _summary_text(panel)

        assert "alpha: one" in content
        assert "beta: two" in content
        assert "gamma: three" in content
        assert "delta: four" in content
        assert "epsilon: five" in content
        assert "showing all attributes; press a to collapse" in content
        assert _panel_height(panel) > DEFAULT_SUMMARY_HEIGHT


@pytest.mark.asyncio
async def test_status_bar_uses_relative_path_for_files_under_cwd(snapshot_hdf5_file: Path) -> None:
    async with HDF5ViewerApp(snapshot_hdf5_file).run_test() as pilot:
        await pilot.pause()
        status_bar = pilot.app.screen.query_one("#status-bar", Static)
        assert "tests/.snapshot-fixtures/sample.h5" in str(status_bar.content)


def _multi_attr_file(tmp_path: Path) -> Path:
    path = tmp_path / "attrs.h5"
    with h5py.File(path, "w") as handle:
        group = handle.create_group("group")
        group.attrs["alpha"] = "one"
        group.attrs["beta"] = "two"
        group.attrs["gamma"] = "three"
        group.attrs["delta"] = "four"
        group.attrs["epsilon"] = "five"
    return path


def _summary_text(panel: SummaryPanel) -> str:
    content = cast(Any, panel.content)
    return "\n".join(str(renderable) for renderable in content.renderables)


def _panel_height(panel: SummaryPanel) -> int:
    height = cast(Any, panel.styles.height)
    return int(height.value)
