"""Backtest package exports.

The backtest package is organized into:
- "engine": the shared position-based execution engine
- strategy-specific modules such as "macd" and "grid" for plotting helpers
  and compatibility wrappers

Most callers should import from this package root so execution, summary, and
plotting entry points stay centralized.
"""

from .engine import run_position_backtest
from .grid import backtest_grid_strategy, plot_grid_backtest
from .macd import backtest_macd_strategy, plot_macd_backtest, summarize_backtest

__all__ = [
    "run_position_backtest",
    "backtest_grid_strategy",
    "plot_grid_backtest",
    "backtest_macd_strategy",
    "plot_macd_backtest",
    "summarize_backtest",
]
