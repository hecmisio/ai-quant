"""CLI inbound adapters."""

from .a_share_cli import run_fetch_command, run_ingest_command
from .kline_cli import run_normalize_command
from .macd_cli import run_macd_backtest_command, run_macd_signal_command

__all__ = [
    "run_fetch_command",
    "run_ingest_command",
    "run_normalize_command",
    "run_macd_backtest_command",
    "run_macd_signal_command",
]
