"""CLI inbound adapters."""

from .a_share_cli import run_fetch_command, run_ingest_command
from .historical_kline_cli import run_ingest_command as run_historical_kline_ingest_command
from .kline_cli import run_normalize_command

__all__ = [
    "run_fetch_command",
    "run_ingest_command",
    "run_historical_kline_ingest_command",
    "run_normalize_command",
]
