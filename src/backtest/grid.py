"""Grid strategy backtest and charting helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.strategies.mean_reversion import GridStrategy

from .charting import plot_strategy_backtest
from .engine import run_position_backtest
from .macd import summarize_backtest


def backtest_grid_strategy(
    data: pd.DataFrame,
    strategy: GridStrategy,
    initial_capital: float = 100000.0,
    position_size: float = 1.0,
    fee_rate: float = 0.0001,
    stamp_duty_rate: float = 0.001,
    slippage_rate: float = 0.0005,
    lot_size: int = 100,
) -> pd.DataFrame:
    """Run a simple A-share style backtest for the grid strategy."""

    return run_position_backtest(
        data,
        strategy,
        initial_capital=initial_capital,
        position_size=position_size,
        fee_rate=fee_rate,
        stamp_duty_rate=stamp_duty_rate,
        slippage_rate=slippage_rate,
        lot_size=lot_size,
    )


def plot_grid_backtest(
    result: pd.DataFrame,
    output_path: str | Path,
    title: str | None = None,
    subtitle: str | None = None,
) -> Path:
    """Render a price/grid/capital chart with buy and sell markers."""

    return plot_strategy_backtest(
        result,
        output_path,
        title,
        subtitle,
        strategy_panel_renderer=_render_grid_panel,
        parameter_section_builder=_build_grid_parameter_section,
        summary_builder=summarize_backtest,
    )


def _build_grid_parameter_section(summary: dict) -> dict:
    params = summary.get("strategy_params", {})
    return {
        "title": "Parameters",
        "lines": [
            ("Lower Bound", f"{params.get('lower_bound', '-'):,.3f}" if params.get("lower_bound") is not None else "-", "#1f2937"),
            ("Upper Bound", f"{params.get('upper_bound', '-'):,.3f}" if params.get("upper_bound") is not None else "-", "#1f2937"),
            ("Grid Count", f"{params.get('grid_count', '-')}", "#1f2937"),
            ("Capital", f"{summary['initial_capital']:,.0f}", "#1f2937"),
            ("Position", f"{summary['position_size']:.0%}", "#1f2937"),
            ("Lot Size", f"{summary['lot_size']}", "#1f2937"),
        ],
    }


def _render_grid_panel(axis, result: pd.DataFrame, x_axis: pd.Series) -> None:
    axis.step(
        x_axis,
        result["target_position"],
        where="post",
        label="Target Position",
        color="#6f4e7c",
        linewidth=1.5,
    )
    axis.fill_between(x_axis, result["target_position"], step="post", alpha=0.14, color="#6f4e7c")
    if "grid_bucket" in result.columns:
        axis.plot(
            x_axis,
            result["grid_bucket"].astype("float"),
            label="Grid Bucket",
            color="#f39c12",
            linewidth=1.0,
            alpha=0.85,
        )
    if "grid_lower_bound" in result.columns:
        axis.plot(x_axis, result["grid_lower_bound"], label="Grid Lower", color="#2ca25f", linestyle="--", linewidth=1.0)
    if "grid_upper_bound" in result.columns:
        axis.plot(x_axis, result["grid_upper_bound"], label="Grid Upper", color="#de2d26", linestyle="--", linewidth=1.0)
    axis.set_ylabel("Grid State")
    axis.legend(loc="upper left")
    axis.grid(alpha=0.25)
