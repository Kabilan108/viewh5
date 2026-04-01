from __future__ import annotations

from pathlib import Path

from textual.app import App
from textual.binding import Binding

from viewh5.model import HDF5Model
from viewh5.screens.main import MainScreen


class HDF5ViewerApp(App[None]):
    BINDINGS = [Binding("q", "quit", "Quit", show=True)]

    def __init__(self, path: Path | str) -> None:
        super().__init__()
        self.model = HDF5Model(path)

    def on_mount(self) -> None:
        self.push_screen(MainScreen(self.model))
