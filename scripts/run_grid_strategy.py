"""Run the grid strategy against a CSV file."""

from __future__ import annotations

import argparse

from _common import load_price_data, write_output_csv
from src.strategies.mean_reversion import GridStrategy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run fixed-range grid strategy on CSV price data.")
    parser.add_argument("input_csv", help="Path to input CSV file with a close column.")
    parser.add_argument("--lower-bound", type=float, required=True)
    parser.add_argument("--upper-bound", type=float, required=True)
    parser.add_argument("--grid-count", type=int, required=True)
    parser.add_argument("--price-column", default="close")
    parser.add_argument(
        "--output-csv",
        help="Optional path for writing the strategy output CSV. Prints preview when omitted.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = load_price_data(args.input_csv)
    strategy = GridStrategy(
        lower_bound=args.lower_bound,
        upper_bound=args.upper_bound,
        grid_count=args.grid_count,
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
