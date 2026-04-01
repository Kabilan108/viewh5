from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PreviewRisk = Literal["safe", "warn", "blocked", "unsupported"]
ObjectKind = Literal["file", "group", "dataset"]
PreviewKind = Literal["scalar", "table_1d", "table_2d", "unsupported", "blocked"]
SearchKind = Literal["group", "dataset"]


@dataclass(slots=True)
class H5ObjectSummary:
    path: str
    name: str
    kind: ObjectKind
    dtype: str | None
    shape: tuple[int, ...] | None
    ndim: int | None
    size: int | None
    nbytes: int | None
    chunks: tuple[int, ...] | None
    compression: str | None
    attrs: list[tuple[str, str]]
    child_count: int | None
    preview_risk: PreviewRisk
    preview_reason: str | None


@dataclass(slots=True)
class H5ChildEntry:
    path: str
    name: str
    kind: Literal["group", "dataset"]
    expandable: bool


@dataclass(slots=True)
class PreviewPage:
    path: str
    kind: PreviewKind
    columns: list[str]
    rows: list[list[str]]
    row_offset: int
    total_rows: int
    column_offset: int
    total_columns: int
    warning: str | None


@dataclass(slots=True)
class SearchHit:
    path: str
    kind: SearchKind
