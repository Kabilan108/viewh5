from __future__ import annotations

from pathlib import Path

from viewh5.model import COLUMN_PAGE_SIZE_2D, HDF5Model, ROW_PAGE_SIZE_1D


def test_root_summary(sample_hdf5_file: Path) -> None:
    model = HDF5Model(sample_hdf5_file)
    summary = model.get_root_summary()
    assert summary.path == "/"
    assert summary.kind == "file"
    assert summary.child_count == 4


def test_list_children_sorts_groups_before_datasets(sample_hdf5_file: Path) -> None:
    model = HDF5Model(sample_hdf5_file)
    children = model.list_children("/")
    assert [child.path for child in children] == ["/group", "/blocked", "/cube", "/scalar"]


def test_group_summary(sample_hdf5_file: Path) -> None:
    model = HDF5Model(sample_hdf5_file)
    summary = model.get_summary("/group")
    assert summary.kind == "group"
    assert summary.child_count == 2
    assert ("note", "root group") in summary.attrs


def test_scalar_preview(sample_hdf5_file: Path) -> None:
    model = HDF5Model(sample_hdf5_file)
    preview = model.get_preview("/scalar")
    assert preview.kind == "scalar"
    assert preview.rows == [["7"]]


def test_vector_preview(sample_hdf5_file: Path) -> None:
    model = HDF5Model(sample_hdf5_file)
    preview = model.get_preview("/group/vector")
    assert preview.kind == "table_1d"
    assert preview.columns == ["index", "value"]
    assert preview.rows[0] == ["0", "0"]
    assert preview.total_rows == 32
    assert preview.row_offset == 0


def test_matrix_preview_with_column_offset(sample_hdf5_file: Path) -> None:
    model = HDF5Model(sample_hdf5_file)
    preview = model.get_preview("/group/matrix", column_offset=3)
    assert preview.kind == "table_2d"
    assert preview.columns[0] == "row"
    assert preview.columns[1] == "3"
    assert preview.rows[0][0] == "0"
    assert preview.rows[0][1] == "3"
    assert preview.column_offset == 3
    assert preview.total_columns == 12
    assert len(preview.columns) == 10
    assert len(preview.rows) == 6


def test_unsupported_preview_for_ndim_above_two(sample_hdf5_file: Path) -> None:
    model = HDF5Model(sample_hdf5_file)
    summary = model.get_summary("/cube")
    preview = model.get_preview("/cube")
    assert summary.preview_risk == "unsupported"
    assert preview.kind == "unsupported"


def test_blocked_preview_requires_force(sample_hdf5_file: Path) -> None:
    model = HDF5Model(sample_hdf5_file)
    summary = model.get_summary("/blocked")
    preview = model.get_preview("/blocked")
    forced_preview = model.get_preview("/blocked", force=True)
    assert summary.preview_risk == "blocked"
    assert preview.kind == "blocked"
    assert forced_preview.kind == "table_1d"
    assert len(forced_preview.rows) == ROW_PAGE_SIZE_1D


def test_search_index_contains_paths(sample_hdf5_file: Path) -> None:
    model = HDF5Model(sample_hdf5_file)
    hits = model.build_search_index()
    assert any(hit.path == "/group/vector" for hit in hits)
    assert any(hit.path == "/group" for hit in hits)


def test_column_page_constant_is_smaller_than_matrix_width() -> None:
    assert COLUMN_PAGE_SIZE_2D < 64
