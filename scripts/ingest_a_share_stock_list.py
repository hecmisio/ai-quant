"""Ingest the normalized A-share stock list into Anne PostgreSQL."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.adapters.inbound.cli.a_share_cli import run_ingest_command


def main() -> None:
    run_ingest_command()


if __name__ == "__main__":
    main()
