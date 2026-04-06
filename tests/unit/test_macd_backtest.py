"""Tests for MACD backtest reporting and chart export."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.backtest import backtest_macd_strategy, plot_macd_backtest, summarize_backtest
from src.strategies.trend import MACDStrategy


def build_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "datetime": pd.date_range("2025-01-01", periods=13, freq="D"),
            "close": [10, 9, 8, 9, 10, 11, 12, 11, 10, 9, 8, 9, 10],
        }
    )


def test_backtest_adds_equity_columns() -> None:
    result = backtest_macd_strategy(build_fixture(), MACDStrategy(fast_period=2, slow_period=3, signal_period=2))

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


def test_summarize_backtest_returns_core_metrics() -> None:
    result = backtest_macd_strategy(
        build_fixture(),
        MACDStrategy(fast_period=2, slow_period=3, signal_period=2),
        initial_capital=200000,
        position_size=0.5,
    )

    summary = summarize_backtest(result)

    assert summary["trading_days"] == len(result)
    assert "strategy_total_return" in summary
    assert "benchmark_total_return" in summary
    assert summary["initial_capital"] == 200000
    assert summary["position_size"] == 0.5
    assert summary["fee_rate"] == 0.0001
    assert summary["stamp_duty_rate"] == 0.001
    assert summary["slippage_rate"] == 0.0005
    assert summary["lot_size"] == 100
    assert "final_strategy_capital" in summary
    assert "total_fees" in summary
    assert "total_stamp_duty" in summary
    assert "total_slippage" in summary
    assert summary["buy_signals"] >= 1


def test_backtest_respects_position_size() -> None:
    strategy = MACDStrategy(fast_period=2, slow_period=3, signal_period=2)
    full_result = backtest_macd_strategy(build_fixture(), strategy, initial_capital=100000, position_size=1.0)
    half_result = backtest_macd_strategy(build_fixture(), strategy, initial_capital=100000, position_size=0.5)

    assert 0 < half_result["position_for_return"].max() <= 0.5
    assert half_result["strategy_capital"].iloc[-1] != full_result["strategy_capital"].iloc[-1]


def test_backtest_applies_fees() -> None:
    strategy = MACDStrategy(fast_period=2, slow_period=3, signal_period=2)
    fee_free = backtest_macd_strategy(build_fixture(), strategy, initial_capital=100000, position_size=1.0, fee_rate=0.0)
    with_fee = backtest_macd_strategy(build_fixture(), strategy, initial_capital=100000, position_size=1.0, fee_rate=0.0001)

    assert with_fee["fee_amount"].sum() > 0
    assert with_fee["strategy_capital"].iloc[-1] < fee_free["strategy_capital"].iloc[-1]


def test_backtest_applies_stamp_duty_and_slippage() -> None:
    strategy = MACDStrategy(fast_period=2, slow_period=3, signal_period=2)
    sell_fixture = pd.DataFrame(
        {
            "datetime": pd.date_range("2025-01-01", periods=16, freq="D"),
            "close": [10, 9, 8, 9, 10, 11, 12, 11, 10, 9, 8, 9, 10, 9, 8, 7],
        }
    )
    clean = backtest_macd_strategy(
        sell_fixture,
        strategy,
        initial_capital=100000,
        position_size=1.0,
        fee_rate=0.0,
        stamp_duty_rate=0.0,
        slippage_rate=0.0,
    )
    with_costs = backtest_macd_strategy(
        sell_fixture,
        strategy,
        initial_capital=100000,
        position_size=1.0,
        fee_rate=0.0,
        stamp_duty_rate=0.001,
        slippage_rate=0.0005,
    )

    assert with_costs["stamp_duty_amount"].sum() > 0
    assert with_costs["slippage_amount"].sum() > 0
    assert with_costs.loc[with_costs["trade_side"] == "buy", "trade_shares"].iloc[0] < clean.loc[
        clean["trade_side"] == "buy", "trade_shares"
    ].iloc[0]


def test_backtest_respects_a_share_lot_size() -> None:
    strategy = MACDStrategy(fast_period=2, slow_period=3, signal_period=2)
    result = backtest_macd_strategy(
        build_fixture(),
        strategy,
        initial_capital=123456,
        position_size=0.73,
        fee_rate=0.0001,
        stamp_duty_rate=0.001,
        slippage_rate=0.0005,
        lot_size=100,
    )

    executed = result.loc[result["trade_side"] == "buy", "trade_shares"]
    assert not executed.empty
    assert all(int(value) % 100 == 0 for value in executed.tolist())


def test_plot_macd_backtest_writes_png() -> None:
    result = backtest_macd_strategy(build_fixture(), MACDStrategy(fast_period=2, slow_period=3, signal_period=2))
    output_path = Path("outputs/reports/test_macd_backtest.png")

    plot_macd_backtest(result, output_path, title="MACD Test Chart")

    assert output_path.exists()
    assert output_path.stat().st_size > 0
