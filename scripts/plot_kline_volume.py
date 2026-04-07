"""Export a single PNG with candlesticks and volume bars on a shared x-axis."""

from __future__ import annotations

import argparse

from _common import default_report_path, filter_by_date, load_price_data, strategy_symbol
from src.backtest import plot_kline_volume_chart


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a combined candlestick and volume chart from K-line CSV data.")
    parser.add_argument("input_csv", help="Path to raw or normalized price CSV.")
    parser.add_argument("--start-date", help="Optional inclusive start date in YYYY-MM-DD format.")
    parser.add_argument("--end-date", help="Optional inclusive end date in YYYY-MM-DD format.")
    parser.add_argument("--chart-png", help="Optional chart PNG path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = load_price_data(args.input_csv)
    data = filter_by_date(data, args.start_date, args.end_date)
    if data.empty:
        raise SystemExit("No rows remain after date filtering.")

    chart_png = args.chart_png or default_report_path(args.input_csv, "kline.volume.png")
    symbol = strategy_symbol(args.input_csv)
    title = f"{symbol} K-line and Volume"

    subtitle = None
    if "datetime" in data.columns:
        subtitle = f"{data['datetime'].iloc[0].date()} -> {data['datetime'].iloc[-1].date()} | Rows {len(data)}"
    else:
        subtitle = f"Rows {len(data)}"

    chart_png = plot_kline_volume_chart(data, chart_png, title=title, subtitle=subtitle)
    print(f"chart_png={chart_png}")


if __name__ == "__main__":
    main()
