from __future__ import annotations

from pathlib import Path

import pytest

from viewh5 import cli


def test_main_runs_tui_for_open_command(
    sample_hdf5_file: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: dict[str, object] = {}

    class FakeApp:
        def __init__(self, path: Path) -> None:
            calls["path"] = path

        def run(self) -> None:
            calls["ran"] = True

    monkeypatch.setattr(cli, "HDF5ViewerApp", FakeApp)

    assert cli.main(["open", str(sample_hdf5_file)]) == 0
    assert calls == {
        "path": sample_hdf5_file.resolve(),
        "ran": True,
    }


def test_main_describe_prints_text_preview(sample_hdf5_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["describe", "--height", "4", str(sample_hdf5_file)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert captured.out == "\n".join(
        [
            "sample.h5",
            "/ [file] children=4",
            "+- group/ [group] children=2 attrs=1",
            "... truncated 11 line(s)",
            "",
        ]
    )


def test_main_describe_rejects_non_positive_dimensions(
    sample_hdf5_file: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as error:
        cli.main(["describe", "--width", "0", str(sample_hdf5_file)])

    captured = capsys.readouterr()
    assert error.value.code == 2
    assert "must be greater than zero" in captured.err


def test_main_help_uses_plain_click_format(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["--help"]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert "Usage: viewh5 [OPTIONS] COMMAND [ARGS]..." in captured.out
    assert "Commands:" in captured.out
    assert "describe" in captured.out
    assert "open" in captured.out
    assert "╭" not in captured.out
    assert "--install-completion" in captured.out
    assert "--show-completion" in captured.out


def test_open_help_uses_plain_click_format(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["open", "--help"]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert "Usage: viewh5 open [OPTIONS] PATH" in captured.out
    assert "╭" not in captured.out


def test_describe_help_uses_plain_click_format(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["describe", "--help"]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert "Usage: viewh5 describe [OPTIONS] PATH" in captured.out
    assert "╭" not in captured.out
