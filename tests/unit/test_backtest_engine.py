"""Tests for the shared position-based backtest engine."""

from __future__ import annotations

import pandas as pd
import pytest

from src.backtest.engine import run_position_backtest
from src.strategies.base import BaseStrategy


class DummyPositionStrategy(BaseStrategy):
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        frame = data.copy()
        frame["signal"] = ["hold", "buy", "hold"]
        return frame

    def build_positions(self, signals: pd.DataFrame) -> pd.DataFrame:
        frame = signals.copy()
        frame["target_position"] = [0.0, 1.0, 1.0]
        return frame

    def get_params(self) -> dict:
        return {"name": "dummy"}


def build_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "datetime": pd.date_range("2025-01-01", periods=3, freq="D"),
            "close": [10.0, 11.0, 12.0],
        }
    )


def test_run_position_backtest_executes_minimal_strategy() -> None:
    result = run_position_backtest(build_fixture(), DummyPositionStrategy(), initial_capital=100000)

    assert "strategy_capital" in result.columns
    assert "benchmark_capital" in result.columns
    assert result.attrs["strategy_params"] == {"name": "dummy"}


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"initial_capital": 0}, "initial_capital must be positive"),
        ({"position_size": 2.0}, "position_size must be between 0 and 1"),
        ({"fee_rate": -0.1}, "fee_rate must not be negative"),
        ({"stamp_duty_rate": -0.1}, "stamp_duty_rate must not be negative"),
        ({"slippage_rate": -0.1}, "slippage_rate must not be negative"),
        ({"lot_size": 0}, "lot_size must be positive"),
    ],
)
def test_run_position_backtest_validates_parameters(kwargs: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        run_position_backtest(build_fixture(), DummyPositionStrategy(), **kwargs)
