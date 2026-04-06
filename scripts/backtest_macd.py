"""Run a simple MACD backtest and export chart artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backtest import backtest_macd_strategy, plot_macd_backtest, summarize_backtest
from src.data import normalize_kline_dataframe, read_csv_with_fallback
from src.strategies.trend import MACDStrategy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backtest MACD strategy and export chart output.")
    parser.add_argument("input_csv", help="Path to raw or normalized price CSV.")
    parser.add_argument("--start-date", help="Optional inclusive start date in YYYY-MM-DD format.")
    parser.add_argument("--end-date", help="Optional inclusive end date in YYYY-MM-DD format.")
    parser.add_argument("--fast-period", type=int, default=12)
    parser.add_argument("--slow-period", type=int, default=26)
    parser.add_argument("--signal-period", type=int, default=9)
    parser.add_argument("--price-column", default="close")
    parser.add_argument("--zero-axis-filter", action="store_true")
    parser.add_argument("--initial-capital", type=float, default=100000.0)
    parser.add_argument("--position-size", type=float, default=1.0, help="Position fraction between 0 and 1.")
    parser.add_argument("--fee-rate", type=float, default=0.0001, help="Transaction fee rate applied to each turnover.")
    parser.add_argument("--stamp-duty-rate", type=float, default=0.001, help="Sell-side stamp duty rate.")
    parser.add_argument("--slippage-rate", type=float, default=0.0005, help="Adverse slippage rate on each trade.")
    parser.add_argument("--lot-size", type=int, default=100, help="Minimum trade lot size.")
    parser.add_argument("--output-csv", help="Optional backtest result CSV path.")
    parser.add_argument("--chart-png", help="Optional chart PNG path.")
    return parser.parse_args()


def default_output_csv(input_csv: str) -> Path:
    return ROOT / "outputs" / "reports" / f"{Path(input_csv).stem}.macd.backtest.csv"


def default_chart_png(input_csv: str) -> Path:
    return ROOT / "outputs" / "reports" / f"{Path(input_csv).stem}.macd.backtest.png"


def filter_by_date(data, start_date: str | None, end_date: str | None):
    if "datetime" not in data.columns:
        return data

    filtered = data.copy()
    if start_date:
        filtered = filtered[filtered["datetime"] >= start_date]
    if end_date:
        filtered = filtered[filtered["datetime"] <= end_date]
    return filtered.reset_index(drop=True)


def main() -> None:
    args = parse_args()
    raw_data, _ = read_csv_with_fallback(args.input_csv)
    data = normalize_kline_dataframe(raw_data)
    data = filter_by_date(data, args.start_date, args.end_date)
    if data.empty:
        raise SystemExit("No rows remain after date filtering.")

    strategy = MACDStrategy(
        fast_period=args.fast_period,
        slow_period=args.slow_period,
        signal_period=args.signal_period,
        zero_axis_filter=args.zero_axis_filter,
        price_column=args.price_column,
    )
    result = backtest_macd_strategy(
        data,
        strategy,
        initial_capital=args.initial_capital,
        position_size=args.position_size,
        fee_rate=args.fee_rate,
        stamp_duty_rate=args.stamp_duty_rate,
        slippage_rate=args.slippage_rate,
        lot_size=args.lot_size,
    )
    summary = summarize_backtest(result)

    output_csv = Path(args.output_csv) if args.output_csv else default_output_csv(args.input_csv)
    chart_png = Path(args.chart_png) if args.chart_png else default_chart_png(args.input_csv)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_csv, index=False)

    symbol = Path(args.input_csv).stem.replace("_KLINE", "")
    title = "MACD Strategy Backtest（MACD策略回测）"
    subtitle = (
        f"{symbol} | {summary['start_date']} -> {summary['end_date']} | "
        f"Capital {args.initial_capital:.0f} | Position {args.position_size:.0%}"
    )
    plot_macd_backtest(result, chart_png, title=title, subtitle=subtitle)

    print(f"output_csv={output_csv}")
    print(f"chart_png={chart_png}")
    for key, value in summary.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
