"""Tests for shared script helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts._common import (
    default_report_path,
    filter_by_date,
    strategy_symbol,
    write_output_csv,
)


def test_filter_by_date_respects_bounds() -> None:
    data = pd.DataFrame(
        {
            "datetime": pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03"]),
            "close": [1.0, 2.0, 3.0],
        }
    )

    result = filter_by_date(data, "2025-01-02", "2025-01-02")

    assert len(result) == 1
    assert float(result.loc[0, "close"]) == 2.0


def test_default_report_path_and_symbol_are_derived_from_input() -> None:
    path = default_report_path("data/raw/600519_KLINE.csv", "grid.backtest.csv")

    assert path.name == "600519_KLINE.grid.backtest.csv"
    assert strategy_symbol("data/raw/600519_KLINE.csv") == "600519"


def test_write_output_csv_creates_parent_directories() -> None:
    output_dir = Path("outputs/reports/test_script_common")
    output_path = output_dir / "result.csv"
    frame = pd.DataFrame({"close": [1.0, 2.0]})

    try:
        written = write_output_csv(frame, output_path)

        assert written == output_path
        assert output_path.exists()
        reloaded = pd.read_csv(output_path)
        assert reloaded["close"].tolist() == [1.0, 2.0]
    finally:
        if output_path.exists():
            output_path.unlink()
        if output_dir.exists():
            output_dir.rmdir()
