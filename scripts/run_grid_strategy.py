"""Run the grid strategy against a CSV file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data import normalize_kline_dataframe, read_csv_with_fallback
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
    data, _ = read_csv_with_fallback(args.input_csv)
    data = normalize_kline_dataframe(data)
    strategy = GridStrategy(
        lower_bound=args.lower_bound,
        upper_bound=args.upper_bound,
        grid_count=args.grid_count,
        price_column=args.price_column,
    )
    result = strategy.run(data)

    if args.output_csv:
        output_path = Path(args.output_csv)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(output_path, index=False)
        print(f"Wrote strategy output to {output_path}")
        return

    preview = result.tail(10).to_string(index=False)
    print(preview)


if __name__ == "__main__":
    main()
