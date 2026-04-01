from __future__ import annotations

from dataclasses import dataclass
from math import prod
from pathlib import Path, PurePosixPath
from typing import Any

import h5py
import numpy as np

from viewh5.types import H5ChildEntry, H5ObjectSummary, PreviewPage, PreviewRisk, SearchHit

ROW_PAGE_SIZE_1D = 256
ROW_PAGE_SIZE_2D = 128
COLUMN_PAGE_SIZE_2D = 32
SAFE_PREVIEW_LIMIT = 64 * 1024 * 1024
WARN_PREVIEW_LIMIT = 256 * 1024 * 1024


@dataclass(slots=True)
class PreviewAssessment:
    risk: PreviewRisk
    reason: str | None
    supported: bool


class HDF5Model:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path).resolve()

    def get_root_summary(self) -> H5ObjectSummary:
        with self._open() as handle:
            attrs = self._format_attrs(handle.attrs)
            return H5ObjectSummary(
                path="/",
                name="/",
                kind="file",
                dtype=None,
                shape=None,
                ndim=None,
                size=None,
                nbytes=None,
                chunks=None,
                compression=None,
                attrs=attrs,
                child_count=len(handle.keys()),
                preview_risk="unsupported",
                preview_reason="Preview is only available for datasets.",
            )

    def list_children(self, path: str) -> list[H5ChildEntry]:
        with self._open() as handle:
            group = self._resolve_group(handle, path)
            items: list[H5ChildEntry] = []
            for name, obj in group.items():
                child_path = self._join_path(path, name)
                if isinstance(obj, h5py.Group):
                    items.append(
                        H5ChildEntry(
                            path=child_path,
                            name=name,
                            kind="group",
                            expandable=True,
                        )
                    )
                elif isinstance(obj, h5py.Dataset):
                    items.append(
                        H5ChildEntry(
                            path=child_path,
                            name=name,
                            kind="dataset",
                            expandable=False,
                        )
                    )
            return sorted(items, key=lambda item: (item.kind != "group", item.name.lower()))

    def get_summary(self, path: str) -> H5ObjectSummary:
        with self._open() as handle:
            if path == "/":
                return self.get_root_summary()
            obj = handle[path]
            attrs = self._format_attrs(obj.attrs)
            if isinstance(obj, h5py.Group):
                return H5ObjectSummary(
                    path=path,
                    name=self._display_name(path),
                    kind="group",
                    dtype=None,
                    shape=None,
                    ndim=None,
                    size=None,
                    nbytes=None,
                    chunks=None,
                    compression=None,
                    attrs=attrs,
                    child_count=len(obj.keys()),
                    preview_risk="unsupported",
                    preview_reason="Preview is only available for datasets.",
                )
            if isinstance(obj, h5py.Dataset):
                assessment = self._assess_preview(obj)
                return H5ObjectSummary(
                    path=path,
                    name=self._display_name(path),
                    kind="dataset",
                    dtype=str(obj.dtype),
                    shape=tuple(int(axis) for axis in obj.shape),
                    ndim=int(obj.ndim),
                    size=int(obj.size),
                    nbytes=int(obj.size * obj.dtype.itemsize),
                    chunks=None if obj.chunks is None else tuple(int(axis) for axis in obj.chunks),
                    compression=obj.compression,
                    attrs=attrs,
                    child_count=None,
                    preview_risk=assessment.risk,
                    preview_reason=assessment.reason,
                )
            raise TypeError(f"Unsupported HDF5 object at {path}")

    def get_preview(
        self,
        path: str,
        row_offset: int = 0,
        column_offset: int = 0,
        force: bool = False,
    ) -> PreviewPage:
        with self._open() as handle:
            if path == "/":
                return self._unsupported_preview(path, "Preview is only available for datasets.")
            obj = handle[path]
            if not isinstance(obj, h5py.Dataset):
                return self._unsupported_preview(path, "Preview is only available for datasets.")

            assessment = self._assess_preview(obj)
            if not assessment.supported:
                return self._unsupported_preview(path, assessment.reason or "Preview is not supported.")
            if assessment.risk in {"warn", "blocked"} and not force:
                return PreviewPage(
                    path=path,
                    kind="blocked",
                    columns=[],
                    rows=[],
                    row_offset=0,
                    total_rows=0,
                    column_offset=0,
                    total_columns=0,
                    warning=assessment.reason,
                )

            if obj.ndim == 0:
                value = self._format_cell(obj[()])
                return PreviewPage(
                    path=path,
                    kind="scalar",
                    columns=["value"],
                    rows=[[value]],
                    row_offset=0,
                    total_rows=1,
                    column_offset=0,
                    total_columns=1,
                    warning=assessment.reason if force and assessment.risk != "safe" else None,
                )

            if obj.ndim == 1:
                total_rows = int(obj.shape[0])
                start = self._normalize_offset(row_offset, total_rows, ROW_PAGE_SIZE_1D)
                stop = min(start + ROW_PAGE_SIZE_1D, total_rows)
                values = obj[start:stop]
                rows = [[str(index), self._format_cell(value)] for index, value in enumerate(values, start=start)]
                return PreviewPage(
                    path=path,
                    kind="table_1d",
                    columns=["index", "value"],
                    rows=rows,
                    row_offset=start,
                    total_rows=total_rows,
                    column_offset=0,
                    total_columns=2,
                    warning=assessment.reason if force and assessment.risk != "safe" else None,
                )

            total_rows = int(obj.shape[0])
            total_columns = int(obj.shape[1])
            start_row = self._normalize_offset(row_offset, total_rows, ROW_PAGE_SIZE_2D)
            start_column = self._normalize_offset(column_offset, total_columns, COLUMN_PAGE_SIZE_2D)
            stop_row = min(start_row + ROW_PAGE_SIZE_2D, total_rows)
            stop_column = min(start_column + COLUMN_PAGE_SIZE_2D, total_columns)
            values = obj[start_row:stop_row, start_column:stop_column]
            columns = ["row"] + [str(index) for index in range(start_column, stop_column)]
            rows = [
                [str(start_row + row_index)]
                + [self._format_cell(value) for value in row]
                for row_index, row in enumerate(values)
            ]
            return PreviewPage(
                path=path,
                kind="table_2d",
                columns=columns,
                rows=rows,
                row_offset=start_row,
                total_rows=total_rows,
                column_offset=start_column,
                total_columns=total_columns,
                warning=assessment.reason if force and assessment.risk != "safe" else None,
            )

    def build_search_index(self) -> list[SearchHit]:
        hits: list[SearchHit] = []
        with self._open() as handle:
            def visit(name: str, obj: h5py.Group | h5py.Dataset) -> None:
                if isinstance(obj, h5py.Group):
                    kind = "group"
                elif isinstance(obj, h5py.Dataset):
                    kind = "dataset"
                else:
                    return
                hits.append(SearchHit(path=f"/{name}" if name else "/", kind=kind))

            handle.visititems(visit)
        return sorted(hits, key=lambda hit: hit.path)

    def _open(self) -> h5py.File:
        return h5py.File(self.path, "r")

    def _resolve_group(self, handle: h5py.File, path: str) -> h5py.File | h5py.Group:
        if path == "/":
            return handle
        obj = handle[path]
        if not isinstance(obj, h5py.Group):
            raise TypeError(f"{path} is not a group")
        return obj

    def _assess_preview(self, dataset: h5py.Dataset) -> PreviewAssessment:
        if not self._is_supported_dtype(dataset.dtype):
            return PreviewAssessment("unsupported", "Preview is not supported for this dataset type.", False)
        if dataset.ndim > 2:
            return PreviewAssessment("unsupported", "Preview is only supported for scalar, 1D, and 2D datasets.", False)

        estimated_read = self._estimate_preview_read(dataset)
        if estimated_read <= SAFE_PREVIEW_LIMIT:
            return PreviewAssessment("safe", None, True)
        if estimated_read <= WARN_PREVIEW_LIMIT:
            return PreviewAssessment(
                "warn",
                f"Preview may read about {self._format_bytes(estimated_read)} because of the storage layout. Press p to load it.",
                True,
            )
        return PreviewAssessment(
            "blocked",
            f"Preview is gated because it may read about {self._format_bytes(estimated_read)}. Press p to load it anyway.",
            True,
        )

    def _estimate_preview_read(self, dataset: h5py.Dataset) -> int:
        if dataset.chunks is not None:
            return int(prod(dataset.chunks) * dataset.dtype.itemsize)
        if dataset.ndim == 0:
            return int(dataset.dtype.itemsize)
        if dataset.ndim == 1:
            return int(min(int(dataset.shape[0]), ROW_PAGE_SIZE_1D) * dataset.dtype.itemsize)
        if dataset.ndim == 2:
            requested = min(int(dataset.shape[0]), ROW_PAGE_SIZE_2D) * min(int(dataset.shape[1]), COLUMN_PAGE_SIZE_2D)
            return int(requested * dataset.dtype.itemsize)
        return int(dataset.dtype.itemsize)

    def _unsupported_preview(self, path: str, warning: str) -> PreviewPage:
        return PreviewPage(
            path=path,
            kind="unsupported",
            columns=[],
            rows=[],
            row_offset=0,
            total_rows=0,
            column_offset=0,
            total_columns=0,
            warning=warning,
        )

    def _is_supported_dtype(self, dtype: np.dtype[Any]) -> bool:
        if dtype.fields is not None:
            return False
        if h5py.check_vlen_dtype(dtype) is not None:
            return False
        if h5py.check_enum_dtype(dtype) is not None:
            return False
        return dtype.kind in {"b", "i", "u", "f", "S", "U"}

    def _format_attrs(self, attrs: h5py.AttributeManager) -> list[tuple[str, str]]:
        return [(str(name), self._stringify_value(attrs[name])) for name in attrs.keys()]

    def _stringify_value(self, value: Any) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        if isinstance(value, str):
            return value
        if isinstance(value, np.ndarray):
            if value.ndim == 0:
                return self._stringify_value(value.item())
            return np.array2string(value, threshold=6)
        if isinstance(value, np.generic):
            return self._stringify_value(value.item())
        if isinstance(value, (list, tuple)):
            return "[" + ", ".join(self._stringify_value(item) for item in value) + "]"
        return str(value)

    def _format_cell(self, value: Any) -> str:
        rendered = self._stringify_value(value)
        return rendered if len(rendered) <= 120 else f"{rendered[:117]}..."

    def _normalize_offset(self, offset: int, total: int, page_size: int) -> int:
        if total <= 0:
            return 0
        max_offset = max(total - 1, 0)
        return max(0, min(offset, max_offset))

    def _join_path(self, parent: str, name: str) -> str:
        if parent == "/":
            return f"/{name}"
        return f"{parent}/{name}"

    def _display_name(self, path: str) -> str:
        if path == "/":
            return "/"
        return PurePosixPath(path).name

    def _format_bytes(self, size: int) -> str:
        units = ["B", "KiB", "MiB", "GiB", "TiB"]
        value = float(size)
        unit = units[0]
        for unit in units:
            if value < 1024 or unit == units[-1]:
                break
            value /= 1024
        return f"{value:.1f} {unit}"
