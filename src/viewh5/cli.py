from __future__ import annotations

import argparse
import sys
from pathlib import Path

import h5py

from viewh5.app import HDF5ViewerApp
from viewh5.describe import DescribeOptions, describe_file
from viewh5.model import HDF5Model


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "describe":
        return _describe_main(args[1:])

    parser = argparse.ArgumentParser(prog="viewh5")
    parser.add_argument("path", help="Path to a local HDF5 file")
    parsed = parser.parse_args(args)
    path = _validate_path(parsed.path)
    if path is None:
        return 2

    app = HDF5ViewerApp(path.resolve())
    app.run()
    return 0


def _describe_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="viewh5 describe")
    parser.add_argument("path", help="Path to a local HDF5 file")
    parser.add_argument("--width", type=_positive_int, default=None)
    parser.add_argument("--height", type=_positive_int, default=None)
    parser.add_argument("--max-depth", type=_positive_int, default=3)
    parser.add_argument("--max-children", type=_positive_int, default=25)
    parser.add_argument("--max-attrs", type=_positive_int, default=6)
    parser.add_argument("--preview-rows", type=_positive_int, default=4)
    parser.add_argument("--preview-columns", type=_positive_int, default=6)
    parsed = parser.parse_args(argv)

    path = _validate_path(parsed.path)
    if path is None:
        return 2

    model = HDF5Model(path)
    print(
        describe_file(
            model,
            DescribeOptions(
                width=parsed.width,
                height=parsed.height,
                max_depth=parsed.max_depth,
                max_children=parsed.max_children,
                max_attrs=parsed.max_attrs,
                preview_rows=parsed.preview_rows,
                preview_columns=parsed.preview_columns,
            ),
        )
    )
    return 0


def _validate_path(path_arg: str) -> Path | None:
    path = Path(path_arg).expanduser()
    if not path.exists():
        print(f"error: {path} does not exist", file=sys.stderr)
        return None
    if not path.is_file():
        print(f"error: {path} is not a file", file=sys.stderr)
        return None

    try:
        with h5py.File(path, "r"):
            pass
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return None
    return path


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed
