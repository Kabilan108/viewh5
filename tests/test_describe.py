from __future__ import annotations

from pathlib import Path

from viewh5.describe import DescribeOptions, describe_file
from viewh5.model import HDF5Model


def test_describe_file_renders_tree(sample_hdf5_file: Path) -> None:
    output = describe_file(HDF5Model(sample_hdf5_file), DescribeOptions())

    assert output == "\n".join(
        [
            "sample.h5",
            "/ [file] children=4",
            "+- group/ [group] children=2 attrs=1",
            "|  @ note = root group",
            "|  +- matrix [dataset] dtype=int64 shape=(6, 12) bytes=576.0 B preview=safe",
            "|  |  = [[0, 1, 2, 3, 4, 5, ...], [10, 11, 12, 13, 14, 15, ...], [20, 21, 22, 23, 24, 25, ...], [30, 31, 32, 33, 34, 35, ...], ...]",
            "|  `- vector [dataset] dtype=int64 shape=(32,) bytes=256.0 B preview=safe",
            "|     = [0, 1, 2, 3, 4, 5, ...]",
            "+- blocked [dataset] dtype=float64 shape=(40000000,) bytes=305.2 MiB chunks=(40000000,) compression=gzip preview=blocked",
            "|  ! Preview is gated because it may read about 305.2 MiB. Press p to load it anyway.",
            "+- cube [dataset] dtype=int64 shape=(2, 2, 2) bytes=64.0 B preview=unsupported",
            "|  ! Preview is only supported for scalar, 1D, and 2D datasets.",
            "`- scalar [dataset] dtype=int64 shape=() bytes=8.0 B preview=safe",
            "   = 7",
        ]
    )


def test_describe_file_applies_width_and_height_limits(sample_hdf5_file: Path) -> None:
    output = describe_file(HDF5Model(sample_hdf5_file), DescribeOptions(width=20, height=6))

    assert output == "\n".join(
        [
            "sample.h5",
            "/ [file] children=4",
            "+- group/ [group]...",
            "|  @ note = root ...",
            "|  +- matrix [dat...",
            "... truncated 9 l...",
        ]
    )
