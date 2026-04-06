"""Pytest test suite for the MACD strategy."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from src.strategies.trend import MACDStrategy


FIXTURE_PATH = Path("tests/fixtures/macd_prices.csv")


def read_fixture_csv(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path)
    if not isinstance(data, pd.DataFrame):
        raise TypeError("expected pandas DataFrame from fixture CSV")
    return data


@pytest.fixture
def fixture_prices() -> pd.DataFrame:
    return read_fixture_csv(FIXTURE_PATH)


def test_indicator_output_contains_macd_columns(fixture_prices: pd.DataFrame) -> None:
    strategy = MACDStrategy(fast_period=2, slow_period=3, signal_period=2)

    result = strategy.generate_signals(fixture_prices)

    assert list(result.index) == list(fixture_prices.index)
    for column in ("dif", "dea", "histogram", "signal", "is_valid_signal_row"):
        assert column in result.columns
    assert result["dif"].notna().any()
    assert result["dea"].notna().any()
    assert result["histogram"].notna().any()


def test_missing_close_column_raises_validation_error() -> None:
    strategy = MACDStrategy()

    with pytest.raises(ValueError, match="include 'close' column"):
        strategy.generate_signals(pd.DataFrame({"price": [1, 2, 3]}))


def test_crossover_signals_are_deterministic(fixture_prices: pd.DataFrame) -> None:
    strategy = MACDStrategy(fast_period=2, slow_period=3, signal_period=2)

    result = strategy.run(fixture_prices)
    buy_rows = result.index[result["signal"] == "buy"].tolist()
    sell_rows = result.index[result["signal"] == "sell"].tolist()

    assert buy_rows == [11]
    assert sell_rows == [7]
    assert result.loc[11, "target_position"] == 1
    assert result.loc[7, "target_position"] == 0


def test_zero_axis_filter_blocks_negative_crossovers() -> None:
    data = pd.DataFrame({"close": [10, 10, 9, 8, 8.4, 8.8, 9.2, 9.0]})
    baseline = MACDStrategy(fast_period=2, slow_period=3, signal_period=2)
    filtered = MACDStrategy(
        fast_period=2,
        slow_period=3,
        signal_period=2,
        zero_axis_filter=True,
    )

    baseline_result = baseline.run(data)
    filtered_result = filtered.run(data)

    assert "buy" in baseline_result["signal"].tolist()
    blocked_index = baseline_result.index[baseline_result["signal"] == "buy"][0]
    assert filtered_result.loc[blocked_index, "signal"] == "hold"
    assert filtered_result.loc[blocked_index, "dif"] < 0
    assert filtered_result.loc[blocked_index, "target_position"] == 0


def test_invalid_rows_stay_flat_and_reset_position() -> None:
    data = pd.DataFrame({"close": [10, 9, 8, 9, 10, 11, None, 12, 13]})
    strategy = MACDStrategy(fast_period=2, slow_period=3, signal_period=2)

    result = strategy.run(data)

    invalid_index = 6
    assert result.loc[invalid_index, "signal"] == "hold"
    assert result.loc[invalid_index, "target_position"] == 0
    assert not result.loc[invalid_index, "is_valid_signal_row"]


def test_macd_helper_methods_compute_indicators_and_signals() -> None:
    data = pd.DataFrame({"close": [10, 9, 8, 9, 10, 11, 12, 11, 10, 9, 8, 9, 10]})
    strategy = MACDStrategy(fast_period=2, slow_period=3, signal_period=2)
    prepared = strategy.prepare_data(data)

    dif, dea, histogram = strategy._compute_indicator_series(prepared["close"])
    valid_row = prepared["close"].notna() & dif.notna() & dea.notna() & histogram.notna()
    signals = strategy._build_signal_series(dif, dea, valid_row)

    assert dif.notna().any()
    assert dea.notna().any()
    assert histogram.notna().any()
    assert signals.iloc[7] == "sell"
    assert signals.iloc[11] == "buy"


def test_script_entry_point_runs() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/run_macd_strategy.py", str(FIXTURE_PATH)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "target_position" in completed.stdout
