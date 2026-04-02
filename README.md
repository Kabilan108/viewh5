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

For a non-interactive summary, use:

```bash
viewh5 describe path/to/file.h5
```

## Yazi Previews

`viewh5` can be used as both the HDF5 opener and the previewer in Yazi. The preview flow is built around `piper.yazi`, which runs `viewh5 describe` and shows the resulting text in Yazi's preview pane.

1. Install `viewh5` so the `viewh5` command is on your `PATH`.

```bash
uv tool install viewh5
```

2. Install the `piper.yazi` plugin:

```bash
ya pkg add yazi-rs/plugins:piper
```

3. Add the opener and preview rules to `~/.config/yazi/yazi.toml`:

```toml
[opener]
h5 = [
  { run = 'viewh5 "$@"', block = true, desc = "View HDF5 file" },
]

[open]
prepend_rules = [
  { url = "*.h5", use = [ "h5" ] },
  { url = "*.hdf5", use = [ "h5" ] },
  { url = "*.hdf", use = [ "h5" ] },
]

[plugin]
prepend_previewers = [
  { url = "*.h5", run = 'piper -- viewh5 describe --width "$w" --height "$h" "$1"' },
  { url = "*.hdf5", run = 'piper -- viewh5 describe --width "$w" --height "$h" "$1"' },
  { url = "*.hdf", run = 'piper -- viewh5 describe --width "$w" --height "$h" "$1"' },
]
```

After restarting Yazi, `open` on an HDF5 file will launch the full Textual app and hovering an HDF5 file will show the text summary in the preview pane.

### Home Manager Setup

If you manage Yazi with Home Manager, the relevant configuration looks like:

```nix
programs.yazi = {
  enable = true;
  enableBashIntegration = true;
  plugins = {
    piper = pkgs.yaziPlugins.piper;
  };
  settings = {
    opener = {
      h5 = [
        { run = ''viewh5 "$@"''; block = true; desc = "View HDF5 file"; }
      ];
    };
    open = {
      prepend_rules = [
        { url = "*.h5"; use = [ "h5" ]; }
        { url = "*.hdf5"; use = [ "h5" ]; }
        { url = "*.hdf"; use = [ "h5" ]; }
      ];
    };
    plugin = {
      prepend_previewers = [
        { url = "*.h5"; run = ''piper -- viewh5 describe --width "$w" --height "$h" "$1"''; }
        { url = "*.hdf5"; run = ''piper -- viewh5 describe --width "$w" --height "$h" "$1"''; }
        { url = "*.hdf"; run = ''piper -- viewh5 describe --width "$w" --height "$h" "$1"''; }
      ];
    };
  };
};
```

After rebuilding Home Manager, `open` on an HDF5 file will launch the full Textual app and hovering an HDF5 file will show the text summary in Yazi's preview pane.

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
