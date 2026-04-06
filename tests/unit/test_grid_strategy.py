"""Pytest test suite for the grid strategy."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from src.strategies.mean_reversion import GridStrategy


FIXTURE_PATH = Path("tests/fixtures/grid_prices.csv")


@pytest.fixture
def fixture_prices() -> pd.DataFrame:
    return pd.read_csv(FIXTURE_PATH)


def test_grid_output_contains_metadata_and_preserves_index(
    fixture_prices: pd.DataFrame,
) -> None:
    strategy = GridStrategy(lower_bound=90, upper_bound=110, grid_count=4)

    result = strategy.generate_signals(fixture_prices)

    assert list(result.index) == list(fixture_prices.index)
    for column in (
        "grid_lower_bound",
        "grid_upper_bound",
        "grid_count",
        "grid_spacing",
        "grid_bucket",
        "grid_bucket_lower",
        "grid_bucket_upper",
        "signal",
        "target_position",
        "is_valid_signal_row",
    ):
        assert column in result.columns
    assert result.attrs["grid_levels"] == [90.0, 95.0, 100.0, 105.0, 110.0]
    assert result.attrs["grid_spacing"] == 5.0


def test_invalid_grid_parameters_raise_validation_error() -> None:
    with pytest.raises(ValueError, match="lower_bound must be less than upper_bound"):
        GridStrategy(lower_bound=100, upper_bound=100, grid_count=4)

    with pytest.raises(ValueError, match="grid_count must be a positive integer"):
        GridStrategy(lower_bound=90, upper_bound=110, grid_count=0)


def test_missing_price_column_raises_validation_error() -> None:
    strategy = GridStrategy(lower_bound=90, upper_bound=110, grid_count=4)

    with pytest.raises(ValueError, match="include 'close' column"):
        strategy.generate_signals(pd.DataFrame({"price": [100, 101, 102]}))


def test_bucket_mapping_and_boundary_saturation_are_deterministic() -> None:
    data = pd.DataFrame({"close": [88, 92, 97, 102, 107, 112]})
    strategy = GridStrategy(lower_bound=90, upper_bound=110, grid_count=4)

    result = strategy.run(data)

    assert result["grid_bucket"].tolist() == [0, 0, 1, 2, 3, 4]
    assert result["target_position"].tolist() == [1.0, 1.0, 0.75, 0.5, 0.25, 0.0]
    assert result.loc[0, "target_position"] == 1.0
    assert result.loc[5, "target_position"] == 0.0


def test_invalid_numeric_rows_fall_back_to_hold_and_zero_position() -> None:
    data = pd.DataFrame({"close": [100, "bad", 94]})
    strategy = GridStrategy(lower_bound=90, upper_bound=110, grid_count=4)

    result = strategy.run(data)

    assert result.loc[1, "signal"] == "hold"
    assert result.loc[1, "target_position"] == 0.0
    assert not result.loc[1, "is_valid_signal_row"]


def test_signal_behavior_covers_single_step_hold_and_multi_step_jump() -> None:
    data = pd.DataFrame({"close": [108, 108, 97, 91, 111]})
    strategy = GridStrategy(lower_bound=90, upper_bound=110, grid_count=4)

    result = strategy.run(data)

    assert result["signal"].tolist() == ["buy", "hold", "buy", "buy", "sell"]
    assert result["target_position"].tolist() == [0.25, 0.25, 0.75, 1.0, 0.0]


def test_grid_row_state_helpers_are_deterministic() -> None:
    strategy = GridStrategy(lower_bound=90, upper_bound=110, grid_count=4)
    grid_levels = strategy._build_grid_levels()

    assert strategy._bucket_bounds(1, grid_levels) == (95.0, 100.0)
    assert strategy._bucket_bounds(4, grid_levels) == (110.0, None)
    assert strategy._signal_for_target_change(0.25, 0.75) == "buy"
    assert strategy._signal_for_target_change(0.75, 0.25) == "sell"
    assert strategy._signal_for_target_change(0.75, 0.75) == "hold"

    row_state = strategy._row_state_for_price(97.0, 0.25, grid_levels)
    assert row_state == {
        "grid_bucket": 1,
        "grid_bucket_lower": 95.0,
        "grid_bucket_upper": 100.0,
        "target_position": 0.75,
        "signal": "buy",
    }


def test_script_entry_point_runs() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_grid_strategy.py",
            str(FIXTURE_PATH),
            "--lower-bound",
            "90",
            "--upper-bound",
            "110",
            "--grid-count",
            "4",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "target_position" in completed.stdout
