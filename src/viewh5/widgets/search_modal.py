from __future__ import annotations

from dataclasses import dataclass

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, OptionList, Static
from textual.widgets._option_list import Option

from viewh5.types import SearchHit


class SearchResults(OptionList):
    BINDINGS = [
        Binding("j,down", "cursor_down", "Down", show=False),
        Binding("k,up", "cursor_up", "Up", show=False),
        Binding("g,home", "first", "First", show=False),
        Binding("G,end", "last", "Last", show=False),
        Binding("enter", "select", "Select", show=False),
    ]


@dataclass(slots=True)
class RankedHit:
    score: tuple[int, int, str]
    hit: SearchHit


class SearchModal(ModalScreen[SearchHit | None]):
    AUTO_FOCUS = "#search-input"
    BINDINGS = [Binding("escape", "dismiss_modal", "Dismiss", show=False)]
    CSS = """
    SearchModal {
        align: center middle;
        background: $background 60%;
    }

    #search-panel {
        width: 80;
        height: 24;
        border: round $border;
        background: $surface;
        padding: 1;
    }

    #search-title {
        padding-bottom: 1;
    }

    #search-input {
        margin-bottom: 1;
    }

    #search-results {
        height: 1fr;
    }
    """

    def __init__(self, hits: list[SearchHit]) -> None:
        super().__init__()
        self.hits = hits
        self.hits_by_path = {hit.path: hit for hit in hits}

    def compose(self) -> ComposeResult:
        with Vertical(id="search-panel"):
            yield Static("Search HDF5 paths", id="search-title")
            yield Input(placeholder="Type part of a path", id="search-input")
            yield SearchResults(id="search-results")

    def on_mount(self) -> None:
        self._update_results("")

    @on(Input.Changed, "#search-input")
    def on_search_changed(self, event: Input.Changed) -> None:
        self._update_results(event.value)

    @on(Input.Submitted, "#search-input")
    def on_search_submitted(self) -> None:
        results = self.query_one(SearchResults)
        if results.highlighted is None:
            return
        results.action_select()

    @on(OptionList.OptionSelected, "#search-results")
    def on_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_id is None:
            self.dismiss(None)
            return
        self.dismiss(self.hits_by_path[event.option_id])

    def action_dismiss_modal(self) -> None:
        self.dismiss(None)

    def _update_results(self, query: str) -> None:
        results = self.query_one(SearchResults)
        ranked = self._filter_hits(query)
        results.clear_options()
        options = [Option(hit.path, id=hit.path) for hit in ranked[:200]]
        results.add_options(options)
        if options:
            results.highlighted = 0

    def _filter_hits(self, query: str) -> list[SearchHit]:
        needle = query.casefold().strip()
        if not needle:
            return self.hits[:200]
        ranked: list[RankedHit] = []
        for hit in self.hits:
            haystack = hit.path.casefold()
            if needle in haystack:
                ranked.append(
                    RankedHit(
                        score=(haystack.find(needle), len(hit.path), hit.path),
                        hit=hit,
                    )
                )
        ranked.sort(key=lambda item: item.score)
        return [item.hit for item in ranked]
