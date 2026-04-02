from __future__ import annotations

from pathlib import Path

import pytest

from viewh5 import cli


def test_main_runs_tui_for_plain_file_argument(
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

    assert cli.main([str(sample_hdf5_file)]) == 0
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
