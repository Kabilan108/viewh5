from __future__ import annotations

from pathlib import Path

import h5py
import pytest


def build_sample_hdf5_file(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(path, "w") as handle:
        root_group = handle.create_group("group")
        root_group.attrs["note"] = "root group"
        root_group.create_dataset("vector", data=list(range(32)))
        root_group.create_dataset(
            "matrix",
            data=[[row * 10 + column for column in range(12)] for row in range(6)],
        )
        handle.create_dataset("scalar", data=7)
        handle.create_dataset(
            "blocked",
            shape=(40_000_000,),
            dtype="float64",
            chunks=(40_000_000,),
            compression="gzip",
        )
        handle.create_dataset("cube", data=[[[1, 2], [3, 4]], [[5, 6], [7, 8]]])
    return path


@pytest.fixture
def sample_hdf5_file(tmp_path: Path) -> Path:
    return build_sample_hdf5_file(tmp_path / "sample.h5")


@pytest.fixture
def snapshot_hdf5_file() -> Path:
    return build_sample_hdf5_file(Path("tests/.snapshot-fixtures/sample.h5").resolve())
