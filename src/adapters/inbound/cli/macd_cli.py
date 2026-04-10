"""CLI adapters for MACD workflows."""

from __future__ import annotations

import argparse

from scripts._common import (
    default_report_path,
    filter_by_date,
    load_price_data,
    strategy_symbol,
    write_output_csv,
)
from src.application.services import (
    MACDBacktestCommand,
    MACDSignalCommand,
    export_macd_backtest_chart,
    run_macd_backtest_workflow,
    run_macd_signal_workflow,
)


def build_signal_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run MACD strategy on CSV price data.")
    parser.add_argument("input_csv", help="Path to input CSV file with a close column.")
    parser.add_argument("--output-csv", help="Optional path for writing the strategy output CSV. Prints preview when omitted.")
    parser.add_argument("--fast-period", type=int, default=12)
    parser.add_argument("--slow-period", type=int, default=26)
    parser.add_argument("--signal-period", type=int, default=9)
    parser.add_argument("--price-column", default="close")
    parser.add_argument("--zero-axis-filter", action="store_true", help="Only allow long entries when DIF is at or above zero.")
    return parser


def run_macd_signal_command() -> None:
    args = build_signal_parser().parse_args()
    data = load_price_data(args.input_csv)
    result = run_macd_signal_workflow(
        data,
        MACDSignalCommand(
            fast_period=args.fast_period,
            slow_period=args.slow_period,
            signal_period=args.signal_period,
            price_column=args.price_column,
            zero_axis_filter=args.zero_axis_filter,
        ),
    )

    if args.output_csv:
        output_path = write_output_csv(result, args.output_csv)
        print(f"Wrote strategy output to {output_path}")
        return

    print(result.tail(10).to_string(index=False))


def build_backtest_parser() -> argparse.ArgumentParser:
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
    return parser


def run_macd_backtest_command() -> None:
    args = build_backtest_parser().parse_args()
    data = load_price_data(args.input_csv)
    data = filter_by_date(data, args.start_date, args.end_date)
    if data.empty:
        raise SystemExit("No rows remain after date filtering.")

    result, summary = run_macd_backtest_workflow(
        data,
        MACDBacktestCommand(
            strategy=MACDSignalCommand(
                fast_period=args.fast_period,
                slow_period=args.slow_period,
                signal_period=args.signal_period,
                price_column=args.price_column,
                zero_axis_filter=args.zero_axis_filter,
            ),
            initial_capital=args.initial_capital,
            position_size=args.position_size,
            fee_rate=args.fee_rate,
            stamp_duty_rate=args.stamp_duty_rate,
            slippage_rate=args.slippage_rate,
            lot_size=args.lot_size,
        ),
    )

    output_csv = args.output_csv or default_report_path(args.input_csv, "macd.backtest.csv")
    chart_png = args.chart_png or default_report_path(args.input_csv, "macd.backtest.png")
    output_csv = write_output_csv(result, output_csv)

    symbol = strategy_symbol(args.input_csv)
    title = "MACD Strategy Backtest"
    subtitle = (
        f"{symbol} | {summary['start_date']} -> {summary['end_date']} | "
        f"Capital {args.initial_capital:.0f} | Position {args.position_size:.0%}"
    )
    export_macd_backtest_chart(result, output_path=chart_png, title=title, subtitle=subtitle)

    print(f"output_csv={output_csv}")
    print(f"chart_png={chart_png}")
    for key, value in summary.items():
        print(f"{key}={value}")
