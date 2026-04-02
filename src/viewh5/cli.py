from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Annotated

import click
import h5py
import typer

from viewh5.app import HDF5ViewerApp
from viewh5.describe import DescribeOptions, describe_file
from viewh5.model import HDF5Model

APP_NAME = "viewh5"


def _validate_path(path_arg: Path) -> Path:
    path = path_arg.expanduser()
    if not path.exists():
        raise typer.BadParameter(f"{path} does not exist")
    if not path.is_file():
        raise typer.BadParameter(f"{path} is not a file")

    try:
        with h5py.File(path, "r"):
            pass
    except OSError as error:
        raise typer.BadParameter(str(error)) from error
    return path


def _positive_int(value: int | None) -> int | None:
    if value is None:
        return None
    if value <= 0:
        raise typer.BadParameter("must be greater than zero")
    return value


app = typer.Typer(
    rich_markup_mode=None,
    pretty_exceptions_enable=False,
)


@app.command("open")
def open_command(
    path: Annotated[
        Path,
        typer.Argument(
            metavar="PATH",
            callback=_validate_path,
        ),
    ],
) -> int:
    viewer = HDF5ViewerApp(path.resolve())
    viewer.run()
    return 0


@app.command()
def describe(
    path: Annotated[
        Path,
        typer.Argument(
            metavar="PATH",
            callback=_validate_path,
        ),
    ],
    width: Annotated[
        int | None,
        typer.Option(callback=_positive_int),
    ] = None,
    height: Annotated[
        int | None,
        typer.Option(callback=_positive_int),
    ] = None,
    max_depth: Annotated[
        int,
        typer.Option("--max-depth", callback=_positive_int),
    ] = 3,
    max_children: Annotated[
        int,
        typer.Option("--max-children", callback=_positive_int),
    ] = 25,
    max_attrs: Annotated[
        int,
        typer.Option("--max-attrs", callback=_positive_int),
    ] = 6,
    preview_rows: Annotated[
        int,
        typer.Option("--preview-rows", callback=_positive_int),
    ] = 4,
    preview_columns: Annotated[
        int,
        typer.Option("--preview-columns", callback=_positive_int),
    ] = 6,
) -> int:
    model = HDF5Model(path)
    print(
        describe_file(
            model,
            DescribeOptions(
                width=width,
                height=height,
                max_depth=max_depth,
                max_children=max_children,
                max_attrs=max_attrs,
                preview_rows=preview_rows,
                preview_columns=preview_columns,
            ),
        )
    )
    return 0


@app.command("version")
def version_command() -> int:
    try:
        print(version(APP_NAME))
    except PackageNotFoundError:
        print("unknown")
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        result = app(args=argv, prog_name=APP_NAME, standalone_mode=False)
    except click.Abort:
        click.echo("Aborted!", err=True)
        raise SystemExit(1) from None
    except click.ClickException as error:
        error.show()
        raise SystemExit(error.exit_code) from None
    return 0 if result is None else int(result)
