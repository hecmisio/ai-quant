"""Normalize a raw K-line CSV file into a UTF-8 standardized dataset."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data import normalize_kline_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert a raw K-line CSV file into UTF-8 with normalized ASCII column names."
    )
    parser.add_argument("input_csv", help="Path to the raw K-line CSV file.")
    parser.add_argument(
        "--output-csv",
        help="Path to the normalized output CSV. Defaults to data/processed/<stem>.normalized.csv",
    )
    return parser


def default_output_path(input_csv: str) -> Path:
    input_path = Path(input_csv)
    return ROOT / "data" / "processed" / f"{input_path.stem}.normalized.csv"


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    output_path = Path(args.output_csv) if args.output_csv else default_output_path(args.input_csv)
    summary = normalize_kline_csv(args.input_csv, output_path)

    print(f"input_path={summary['input_path']}")
    print(f"output_path={summary['output_path']}")
    print(f"source_encoding={summary['source_encoding']}")
    print(f"rows={summary['rows']}")
    print("columns=" + ",".join(summary["columns"]))


if __name__ == "__main__":
    main()
