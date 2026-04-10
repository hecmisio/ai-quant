"""Run a simple MACD backtest and export chart artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.adapters.inbound.cli.macd_cli import run_macd_backtest_command


def main() -> None:
    run_macd_backtest_command()


if __name__ == "__main__":
    main()
