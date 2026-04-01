from __future__ import annotations

import argparse
import sys
from pathlib import Path

import h5py

from viewh5.app import HDF5ViewerApp


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="viewh5")
    parser.add_argument("path", help="Path to a local HDF5 file")
    args = parser.parse_args(argv)

    path = Path(args.path).expanduser()
    if not path.exists():
        print(f"error: {path} does not exist", file=sys.stderr)
        return 2
    if not path.is_file():
        print(f"error: {path} is not a file", file=sys.stderr)
        return 2

    try:
        with h5py.File(path, "r"):
            pass
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    app = HDF5ViewerApp(path.resolve())
    app.run()
    return 0
