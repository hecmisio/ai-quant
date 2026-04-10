"""Application services for MACD workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.backtest import backtest_macd_strategy, plot_macd_backtest, summarize_backtest
from src.domain.strategies import MACDStrategy


@dataclass(frozen=True)
class MACDSignalCommand:
    fast_period: int = 12
    slow_period: int = 26
    signal_period: int = 9
    price_column: str = "close"
    zero_axis_filter: bool = False


@dataclass(frozen=True)
class MACDBacktestCommand:
    strategy: MACDSignalCommand
    initial_capital: float = 100000.0
    position_size: float = 1.0
    fee_rate: float = 0.0001
    stamp_duty_rate: float = 0.001
    slippage_rate: float = 0.0005
    lot_size: int = 100


def build_macd_strategy(command: MACDSignalCommand) -> MACDStrategy:
    return MACDStrategy(
        fast_period=command.fast_period,
        slow_period=command.slow_period,
        signal_period=command.signal_period,
        zero_axis_filter=command.zero_axis_filter,
        price_column=command.price_column,
    )


def run_macd_signal_workflow(data: pd.DataFrame, command: MACDSignalCommand) -> pd.DataFrame:
    strategy = build_macd_strategy(command)
    return strategy.run(data)


def run_macd_backtest_workflow(data: pd.DataFrame, command: MACDBacktestCommand) -> tuple[pd.DataFrame, dict]:
    strategy = build_macd_strategy(command.strategy)
    result = backtest_macd_strategy(
        data,
        strategy,
        initial_capital=command.initial_capital,
        position_size=command.position_size,
        fee_rate=command.fee_rate,
        stamp_duty_rate=command.stamp_duty_rate,
        slippage_rate=command.slippage_rate,
        lot_size=command.lot_size,
    )
    return result, summarize_backtest(result)


def export_macd_backtest_chart(
    result: pd.DataFrame,
    *,
    output_path: str | Path,
    title: str | None = None,
    subtitle: str | None = None,
) -> Path:
    return plot_macd_backtest(result, output_path, title=title, subtitle=subtitle)
