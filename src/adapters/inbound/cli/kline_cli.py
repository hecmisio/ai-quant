"""CLI adapter for K-line normalization."""

from __future__ import annotations

import argparse
from pathlib import Path

from scripts._common import ROOT
from src.adapters.outbound.filesystem import normalize_kline_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert a raw K-line CSV file into UTF-8 with normalized ASCII column names."
    )
    parser.add_argument("input_csv", help="Path to the raw K-line CSV file.")
    parser.add_argument("--output-csv", help="Path to the normalized output CSV. Defaults to data/processed/<stem>.normalized.csv")
    return parser


def default_output_path(input_csv: str) -> Path:
    input_path = Path(input_csv)
    return ROOT / "data" / "processed" / f"{input_path.stem}.normalized.csv"


def run_normalize_command() -> None:
    parser = build_parser()
    args = parser.parse_args()
    output_path = Path(args.output_csv) if args.output_csv else default_output_path(args.input_csv)
    summary = normalize_kline_csv(args.input_csv, output_path)

    print(f"input_path={summary['input_path']}")
    print(f"output_path={summary['output_path']}")
    print(f"source_encoding={summary['source_encoding']}")
    print(f"rows={summary['rows']}")
    print("columns=" + ",".join(summary["columns"]))
