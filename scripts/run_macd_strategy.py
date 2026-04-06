"""Run the MACD strategy against a CSV file."""

from __future__ import annotations

import argparse

from _common import load_price_data, write_output_csv
from src.strategies.trend import MACDStrategy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MACD strategy on CSV price data.")
    parser.add_argument("input_csv", help="Path to input CSV file with a close column.")
    parser.add_argument(
        "--output-csv",
        help="Optional path for writing the strategy output CSV. Prints preview when omitted.",
    )
    parser.add_argument("--fast-period", type=int, default=12)
    parser.add_argument("--slow-period", type=int, default=26)
    parser.add_argument("--signal-period", type=int, default=9)
    parser.add_argument("--price-column", default="close")
    parser.add_argument(
        "--zero-axis-filter",
        action="store_true",
        help="Only allow long entries when DIF is at or above zero.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = load_price_data(args.input_csv)
    strategy = MACDStrategy(
        fast_period=args.fast_period,
        slow_period=args.slow_period,
        signal_period=args.signal_period,
        zero_axis_filter=args.zero_axis_filter,
        price_column=args.price_column,
    )
    result = strategy.run(data)

    if args.output_csv:
        output_path = write_output_csv(result, args.output_csv)
        print(f"Wrote strategy output to {output_path}")
        return

    preview = result.tail(10).to_string(index=False)
    print(preview)


if __name__ == "__main__":
    main()
