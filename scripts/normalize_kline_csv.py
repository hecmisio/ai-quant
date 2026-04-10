"""Normalize a raw K-line CSV file into a UTF-8 standardized dataset."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.adapters.inbound.cli.kline_cli import run_normalize_command


def main() -> None:
    run_normalize_command()


if __name__ == "__main__":
    main()
