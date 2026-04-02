from __future__ import annotations

from dataclasses import dataclass

import h5py

from viewh5.model import HDF5Model

INLINE_PREVIEW_READ_LIMIT = 256 * 1024


@dataclass(slots=True, frozen=True)
class DescribeOptions:
    width: int | None = None
    height: int | None = None
    max_depth: int = 3
    max_children: int = 25
    max_attrs: int = 6
    preview_rows: int = 4
    preview_columns: int = 6


def describe_file(model: HDF5Model, options: DescribeOptions) -> str:
    with model._open() as handle:
        lines = [
            model.path.name,
            _render_file_line(handle),
        ]
        lines.extend(_render_attrs(model, handle.attrs, "", options))
        lines.extend(_render_group_children(model, handle, depth=1, prefix="", options=options))

    if options.height is not None and len(lines) > options.height:
        visible_lines = max(options.height - 1, 0)
        hidden_lines = len(lines) - visible_lines
        lines = lines[:visible_lines]
        lines.append(f"... truncated {hidden_lines} line(s)")

    if options.width is not None:
        lines = [_truncate_line(line, options.width) for line in lines]

    return "\n".join(lines)


def _render_group_children(
    model: HDF5Model,
    group: h5py.File | h5py.Group,
    depth: int,
    prefix: str,
    options: DescribeOptions,
) -> list[str]:
    child_entries = _sorted_group_items(group)
    if not child_entries:
        return []

    lines: list[str] = []
    visible_entries = child_entries[: options.max_children]
    for index, (name, child) in enumerate(visible_entries):
        is_last = index == len(visible_entries) - 1 and len(child_entries) <= options.max_children
        lines.extend(_render_node(model, child, name, depth, prefix, is_last, options))

    hidden_children = len(child_entries) - len(visible_entries)
    if hidden_children > 0:
        lines.append(f"{prefix}+- ... {hidden_children} more child(ren)")
    return lines


def _render_node(
    model: HDF5Model,
    obj: h5py.Group | h5py.Dataset,
    name: str,
    depth: int,
    prefix: str,
    is_last: bool,
    options: DescribeOptions,
) -> list[str]:
    connector = "`- " if is_last else "+- "
    child_prefix = prefix + ("   " if is_last else "|  ")

    if isinstance(obj, h5py.Group):
        lines = [f"{prefix}{connector}{_render_group_summary(obj, name)}"]
        lines.extend(_render_attrs(model, obj.attrs, child_prefix, options))
        if depth >= options.max_depth:
            if obj.keys():
                lines.append(f"{child_prefix}... max depth reached")
            return lines

        lines.extend(_render_group_children(model, obj, depth + 1, child_prefix, options))
        return lines

    lines = [f"{prefix}{connector}{_render_dataset_summary(model, obj, name)}"]
    lines.extend(_render_attrs(model, obj.attrs, child_prefix, options))
    assessment = model._assess_preview(obj)
    if assessment.reason:
        lines.append(f"{child_prefix}! {assessment.reason}")
    sample = _render_dataset_sample(model, obj, options)
    if sample is not None:
        lines.append(f"{child_prefix}= {sample}")
    return lines


def _render_attrs(
    model: HDF5Model,
    attrs: h5py.AttributeManager,
    prefix: str,
    options: DescribeOptions,
) -> list[str]:
    formatted = model._format_attrs(attrs)
    if not formatted:
        return []

    visible_attrs = formatted[: options.max_attrs]
    lines = [f"{prefix}@ {key} = {value}" for key, value in visible_attrs]
    hidden_attrs = len(formatted) - len(visible_attrs)
    if hidden_attrs > 0:
        lines.append(f"{prefix}@ ... {hidden_attrs} more attribute(s)")
    return lines


def _render_dataset_sample(model: HDF5Model, dataset: h5py.Dataset, options: DescribeOptions) -> str | None:
    assessment = model._assess_preview(dataset)
    if not assessment.supported or assessment.risk != "safe":
        return None
    if model._estimate_preview_read(dataset) > INLINE_PREVIEW_READ_LIMIT:
        return None

    if dataset.ndim == 0:
        return model._format_cell(dataset[()])
    if dataset.ndim == 1:
        count = min(int(dataset.shape[0]), options.preview_columns)
        values = [model._format_cell(value) for value in dataset[:count]]
        return _render_sequence(values, has_more=int(dataset.shape[0]) > count)
    if dataset.ndim == 2:
        row_count = min(int(dataset.shape[0]), options.preview_rows)
        column_count = min(int(dataset.shape[1]), options.preview_columns)
        values = dataset[:row_count, :column_count]
        rendered_rows = [
            _render_sequence([model._format_cell(value) for value in row], has_more=int(dataset.shape[1]) > column_count)
            for row in values
        ]
        return _render_sequence(rendered_rows, has_more=int(dataset.shape[0]) > row_count)
    return None


def _render_file_line(handle: h5py.File) -> str:
    parts = ["/ [file]", f"children={len(handle.keys())}"]
    attr_count = len(handle.attrs.keys())
    if attr_count:
        parts.append(f"attrs={attr_count}")
    return " ".join(parts)


def _render_group_summary(group: h5py.Group, name: str) -> str:
    parts = [f"{name}/ [group]", f"children={len(group.keys())}"]
    attr_count = len(group.attrs.keys())
    if attr_count:
        parts.append(f"attrs={attr_count}")
    return " ".join(parts)


def _render_dataset_summary(model: HDF5Model, dataset: h5py.Dataset, name: str) -> str:
    assessment = model._assess_preview(dataset)
    parts = [
        f"{name} [dataset]",
        f"dtype={dataset.dtype}",
        f"shape={tuple(int(axis) for axis in dataset.shape)}",
        f"bytes={model._format_bytes(int(dataset.size * dataset.dtype.itemsize))}",
    ]
    if dataset.chunks is not None:
        parts.append(f"chunks={tuple(int(axis) for axis in dataset.chunks)}")
    if dataset.compression is not None:
        parts.append(f"compression={dataset.compression}")
    parts.append(f"preview={assessment.risk}")
    return " ".join(parts)


def _render_sequence(values: list[str], *, has_more: bool) -> str:
    tail = ", ..." if has_more else ""
    return f"[{', '.join(values)}{tail}]"


def _sorted_group_items(group: h5py.File | h5py.Group) -> list[tuple[str, h5py.Group | h5py.Dataset]]:
    children: list[tuple[str, h5py.Group | h5py.Dataset]] = []
    for name, obj in group.items():
        if isinstance(obj, (h5py.Group, h5py.Dataset)):
            children.append((name, obj))
    return sorted(children, key=lambda item: (not isinstance(item[1], h5py.Group), item[0].lower()))


def _truncate_line(line: str, width: int) -> str:
    if width <= 0:
        return ""
    if len(line) <= width:
        return line
    if width <= 3:
        return "." * width
    return f"{line[: width - 3]}..."
