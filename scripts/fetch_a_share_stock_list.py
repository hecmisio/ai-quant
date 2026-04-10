"""Fetch the A-share stock universe and exclude ST and B shares by default."""

from __future__ import annotations

import argparse

from _common import write_output_csv
from src.data import fetch_a_share_stock_list


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch the A-share stock list with AkShare.")
    parser.add_argument(
        "--include-st",
        action="store_true",
        help="Include ST and *ST stocks in the output. B shares are still excluded.",
    )
    parser.add_argument(
        "--output-csv",
        help="Optional path for writing the filtered stock list to CSV.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stock_list = fetch_a_share_stock_list(include_st=args.include_st)

    if args.output_csv:
        output_path = write_output_csv(stock_list, args.output_csv)
        print(f"Wrote stock list to {output_path}")
        return

    print(stock_list.to_string(index=False))


if __name__ == "__main__":
    main()
