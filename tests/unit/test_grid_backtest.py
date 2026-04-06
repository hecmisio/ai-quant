"""Tests for grid backtest reporting and chart export."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

from src.backtest import backtest_grid_strategy, plot_grid_backtest, summarize_backtest
from src.strategies.mean_reversion import GridStrategy


def build_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "datetime": pd.date_range("2025-01-01", periods=8, freq="D"),
            "close": [108, 103, 97, 92, 89, 95, 101, 111],
        }
    )


def test_backtest_grid_adds_equity_columns() -> None:
    result = backtest_grid_strategy(build_fixture(), GridStrategy(lower_bound=90, upper_bound=110, grid_count=4))

    for column in (
        "daily_return",
        "position_for_return",
        "trade_turnover",
        "gross_strategy_return",
        "fee_return",
        "stamp_duty_return",
        "slippage_return",
        "fee_amount",
        "stamp_duty_amount",
        "slippage_amount",
        "strategy_return",
        "benchmark_equity",
        "strategy_equity",
        "strategy_capital",
        "benchmark_capital",
        "cash_exposure",
        "shares",
        "trade_shares",
        "trade_side",
        "drawdown",
        "benchmark_drawdown",
    ):
        assert column in result.columns


def test_summarize_grid_backtest_returns_core_metrics() -> None:
    result = backtest_grid_strategy(
        build_fixture(),
        GridStrategy(lower_bound=90, upper_bound=110, grid_count=4),
        initial_capital=200000,
        position_size=0.5,
    )

    summary = summarize_backtest(result)

    assert summary["trading_days"] == len(result)
    assert summary["initial_capital"] == 200000
    assert summary["position_size"] == 0.5
    assert "strategy_total_return" in summary
    assert "benchmark_total_return" in summary
    assert summary["buy_signals"] >= 1


def test_plot_grid_backtest_writes_png() -> None:
    result = backtest_grid_strategy(build_fixture(), GridStrategy(lower_bound=90, upper_bound=110, grid_count=4))
    output_path = Path("outputs/reports/test_grid_backtest.png")

    plot_grid_backtest(result, output_path, title="Grid Test Chart")

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_grid_backtest_script_runs() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/backtest_grid.py",
            "tests/fixtures/grid_prices.csv",
            "--lower-bound",
            "90",
            "--upper-bound",
            "110",
            "--grid-count",
            "4",
            "--chart-png",
            "outputs/reports/test_grid_script.png",
            "--output-csv",
            "outputs/reports/test_grid_script.csv",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "chart_png=outputs" in completed.stdout or "chart_png=D:" in completed.stdout
