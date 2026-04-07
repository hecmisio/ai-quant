"""Tests for combined K-line and volume chart export."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from scripts._common import default_report_path
from src.backtest import plot_kline_volume_chart


def build_fixture(with_datetime: bool = True) -> pd.DataFrame:
    data = {
        "open": [10.0, 10.5, 10.2, 10.8],
        "high": [10.8, 10.9, 10.7, 11.2],
        "low": [9.9, 10.1, 10.0, 10.4],
        "close": [10.6, 10.2, 10.6, 11.0],
        "volume": [1000, 1400, 900, 1600],
    }
    if with_datetime:
        data["datetime"] = pd.date_range("2025-01-01", periods=4, freq="D")
    return pd.DataFrame(data)


def test_plot_kline_volume_chart_writes_png() -> None:
    output_path = Path("outputs/reports/test_kline_volume_chart.png")

    plot_kline_volume_chart(build_fixture(), output_path, title="K-line Volume Test")

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_kline_volume_chart_supports_missing_datetime() -> None:
    output_path = Path("outputs/reports/test_kline_volume_no_datetime.png")

    plot_kline_volume_chart(build_fixture(with_datetime=False), output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_kline_volume_chart_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        plot_kline_volume_chart(pd.DataFrame(columns=["open", "high", "low", "close", "volume"]), "ignored.png")


def test_plot_kline_volume_chart_rejects_missing_columns() -> None:
    with pytest.raises(ValueError, match="must include columns"):
        plot_kline_volume_chart(pd.DataFrame({"close": [1.0], "volume": [100]}), "ignored.png")


def test_plot_kline_volume_script_uses_default_report_path() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/plot_kline_volume.py", "tests/fixtures/kline_volume_prices.csv"],
        check=True,
        capture_output=True,
        text=True,
    )

    expected = default_report_path("tests/fixtures/kline_volume_prices.csv", "kline.volume.png")
    assert f"chart_png={expected}" in completed.stdout
    assert expected.exists()
    assert expected.stat().st_size > 0


def test_plot_kline_volume_script_respects_explicit_output_path() -> None:
    output_path = Path("outputs/reports/test_kline_volume_script.png")

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/plot_kline_volume.py",
            "tests/fixtures/kline_volume_prices.csv",
            "--chart-png",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert f"chart_png={output_path}" in completed.stdout or f"chart_png={output_path.resolve()}" in completed.stdout
    assert output_path.exists()
    assert output_path.stat().st_size > 0
