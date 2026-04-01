# viewh5

Read-only, keyboard-first HDF5 viewer built with Textual.

## Install

```bash
uv tool install --from git+https://github.com/kabilan108/viewh5 viewh5
```

Run it with `viewh5 path/to/file.h5`.

## Development

```bash
uv sync
uv run pytest
uv run ruff check
uv run ty check
uv run viewh5 data/1520.h5
```

To update snapshots after making changes to the TUI:

```bash
uv run pytest tests/test_snapshots.py --snapshot-update
```
