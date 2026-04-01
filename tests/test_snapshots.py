from __future__ import annotations

from pathlib import Path

from viewh5.app import HDF5ViewerApp


def test_snapshot_initial(snapshot_hdf5_file: Path, snap_compare) -> None:
    app = HDF5ViewerApp(snapshot_hdf5_file)
    assert snap_compare(app, terminal_size=(120, 36))


def test_snapshot_safe_preview(snapshot_hdf5_file: Path, snap_compare) -> None:
    app = HDF5ViewerApp(snapshot_hdf5_file)

    async def run_before(pilot) -> None:
        await pilot.pause()
        await pilot.press("j", "l", "j")
        await pilot.pause()

    assert snap_compare(app, run_before=run_before, terminal_size=(120, 36))


def test_snapshot_blocked_preview_warning(snapshot_hdf5_file: Path, snap_compare) -> None:
    app = HDF5ViewerApp(snapshot_hdf5_file)

    async def run_before(pilot) -> None:
        await pilot.pause()
        await pilot.press("j", "j")
        await pilot.pause()

    assert snap_compare(app, run_before=run_before, terminal_size=(120, 36))
