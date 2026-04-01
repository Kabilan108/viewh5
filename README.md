# viewh5

[![PyPI](https://img.shields.io/pypi/v/viewh5)](https://pypi.org/project/viewh5/)
[![License](https://img.shields.io/badge/license-AGPL--3.0-blue)](https://pypi.org/project/viewh5/)

Read-only, keyboard-first HDF5 viewer built with Textual.

![viewh5 demo](assets/viewh5-demo.gif)

## Install

```bash
uv tool install viewh5
```

Or install the latest version directly from GitHub:

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
vhs assets/viewh5-demo.tape
```

To update snapshots after making changes to the TUI:

```bash
uv run pytest tests/test_snapshots.py --snapshot-update
```

To recreate the demo, make sure the project environment is synced and `data/waveforms.h5` is present, then run `vhs assets/viewh5-demo.tape`.
