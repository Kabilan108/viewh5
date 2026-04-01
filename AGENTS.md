# viewh5 package notes

- `HDF5ViewerApp` is intentionally thin; nearly all UI behavior is coordinated in `screens/main.py` against `HDF5Model`. Changes to selection, preview paging, or status text usually need matching updates in `tests/test_app.py` and the snapshot baselines.

- `HDF5Model` resolves the file path once and every read opens a fresh `h5py.File(..., "r")`. Keep widget state free of live HDF5 objects and preserve the metadata-first flow that avoids dataset payload reads on startup.

- Snapshot tests render the full Textual screen, so machine-specific strings in the UI will cause CI-only failures. Status text for repo fixtures should stay relative to `Path.cwd()` rather than embedding absolute workspace paths.

- Search is intentionally lazy: the tree only loads root children at startup, group children on expansion, and the full search index only after `/`. Avoid changes that scan the full file during mount or selection changes.
