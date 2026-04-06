"""Run a simple grid-strategy backtest and export chart artifacts."""

from __future__ import annotations

import argparse

from _common import (
    default_report_path,
    filter_by_date,
    load_price_data,
    strategy_symbol,
    write_output_csv,
)
from src.backtest import backtest_grid_strategy, plot_grid_backtest, summarize_backtest
from src.strategies.mean_reversion import GridStrategy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backtest grid strategy and export chart output.")
    parser.add_argument("input_csv", help="Path to raw or normalized price CSV.")
    parser.add_argument("--start-date", help="Optional inclusive start date in YYYY-MM-DD format.")
    parser.add_argument("--end-date", help="Optional inclusive end date in YYYY-MM-DD format.")
    parser.add_argument("--lower-bound", type=float, help="Explicit grid lower bound.")
    parser.add_argument("--upper-bound", type=float, help="Explicit grid upper bound.")
    parser.add_argument("--grid-count", type=int, default=8)
    parser.add_argument("--lower-quantile", type=float, default=0.1)
    parser.add_argument("--upper-quantile", type=float, default=0.9)
    parser.add_argument("--price-column", default="close")
    parser.add_argument("--initial-capital", type=float, default=1000000.0)
    parser.add_argument("--position-size", type=float, default=1.0, help="Position fraction between 0 and 1.")
    parser.add_argument("--fee-rate", type=float, default=0.0001, help="Transaction fee rate applied to each turnover.")
    parser.add_argument("--stamp-duty-rate", type=float, default=0.001, help="Sell-side stamp duty rate.")
    parser.add_argument("--slippage-rate", type=float, default=0.0005, help="Adverse slippage rate on each trade.")
    parser.add_argument("--lot-size", type=int, default=100, help="Minimum trade lot size.")
    parser.add_argument("--output-csv", help="Optional backtest result CSV path.")
    parser.add_argument("--chart-png", help="Optional chart PNG path.")
    return parser.parse_args()


def resolve_bounds(
    data,
    price_column: str,
    lower_bound: float | None,
    upper_bound: float | None,
    lower_quantile: float,
    upper_quantile: float,
) -> tuple[float, float]:
    if lower_bound is not None and upper_bound is not None:
        return float(lower_bound), float(upper_bound)
    if not 0 <= lower_quantile < upper_quantile <= 1:
        raise ValueError("quantiles must satisfy 0 <= lower_quantile < upper_quantile <= 1")
    price_series = data[price_column]
    return float(price_series.quantile(lower_quantile)), float(price_series.quantile(upper_quantile))


def main() -> None:
    args = parse_args()
    data = load_price_data(args.input_csv)
    data = filter_by_date(data, args.start_date, args.end_date)
    if data.empty:
        raise SystemExit("No rows remain after date filtering.")

    lower_bound, upper_bound = resolve_bounds(
        data,
        args.price_column,
        args.lower_bound,
        args.upper_bound,
        args.lower_quantile,
        args.upper_quantile,
    )
    strategy = GridStrategy(
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        grid_count=args.grid_count,
        price_column=args.price_column,
    )
    result = backtest_grid_strategy(
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

    output_csv = args.output_csv or default_report_path(args.input_csv, "grid.backtest.csv")
    chart_png = args.chart_png or default_report_path(args.input_csv, "grid.backtest.png")

    output_csv = write_output_csv(result, output_csv)

    symbol = strategy_symbol(args.input_csv)
    title = "Grid Strategy Backtest"
    subtitle = (
        f"{symbol} | {summary['start_date']} -> {summary['end_date']} | "
        f"Grid {lower_bound:.2f}-{upper_bound:.2f} x {args.grid_count}"
    )
    plot_grid_backtest(result, chart_png, title=title, subtitle=subtitle)

    print(f"output_csv={output_csv}")
    print(f"chart_png={chart_png}")
    print(f"lower_bound={lower_bound}")
    print(f"upper_bound={upper_bound}")
    for key, value in summary.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
