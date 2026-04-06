"""Simple MACD backtest and charting helpers."""

from __future__ import annotations

import os
from pathlib import Path

MPL_CONFIG_DIR = Path(__file__).resolve().parents[2] / ".cache" / "matplotlib"
MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CONFIG_DIR))

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans SC",
    "DejaVu Sans",
]
matplotlib.rcParams["axes.unicode_minus"] = False

import pandas as pd

from src.strategies.trend import MACDStrategy

from .charting import extract_trades, format_start_or_end, plot_strategy_backtest


def backtest_macd_strategy(
    data: pd.DataFrame,
    strategy: MACDStrategy,
    initial_capital: float = 100000.0,
    position_size: float = 1.0,
    fee_rate: float = 0.0001,
    stamp_duty_rate: float = 0.001,
    slippage_rate: float = 0.0005,
    lot_size: int = 100,
) -> pd.DataFrame:
    """Run a simple A-share style MACD backtest with discrete share execution."""

    if initial_capital <= 0:
        raise ValueError("initial_capital must be positive")
    if not 0 <= position_size <= 1:
        raise ValueError("position_size must be between 0 and 1")
    if fee_rate < 0:
        raise ValueError("fee_rate must not be negative")
    if stamp_duty_rate < 0:
        raise ValueError("stamp_duty_rate must not be negative")
    if slippage_rate < 0:
        raise ValueError("slippage_rate must not be negative")
    if lot_size <= 0:
        raise ValueError("lot_size must be positive")

    result = strategy.run(data).copy()
    result["daily_return"] = result["close"].pct_change().fillna(0.0)
    result["benchmark_equity"] = (1.0 + result["daily_return"]).cumprod()
    result["benchmark_capital"] = initial_capital * result["benchmark_equity"]

    target_state = result["target_position"].shift(1).fillna(0.0)

    cash = float(initial_capital)
    shares = 0
    state_rows: list[dict] = []

    for idx, row in result.iterrows():
        price = float(row["close"])
        desired_state = float(target_state.loc[idx]) * position_size
        starting_cash = cash
        starting_shares = shares

        trade_shares = 0
        trade_side = "hold"
        fee_amount = 0.0
        stamp_duty_amount = 0.0
        slippage_amount = 0.0
        trade_notional = 0.0
        execution_price = price
        order_value = 0.0

        if desired_state <= 0 and shares > 0:
            execution_price = price * (1.0 - slippage_rate)
            trade_shares = -shares
            trade_notional = abs(trade_shares) * execution_price
            fee_amount = trade_notional * fee_rate
            stamp_duty_amount = trade_notional * stamp_duty_rate
            slippage_amount = abs(trade_shares) * price * slippage_rate
            cash += trade_notional - fee_amount - stamp_duty_amount
            shares = 0
            trade_side = "sell"

        elif desired_state > 0 and shares == 0:
            execution_price = price * (1.0 + slippage_rate)
            equity_before_trade = cash
            order_value = equity_before_trade * desired_state
            max_lots = int(order_value // (execution_price * lot_size))
            candidate_shares = max_lots * lot_size

            while candidate_shares > 0:
                trade_notional = candidate_shares * execution_price
                fee_amount = trade_notional * fee_rate
                total_cost = trade_notional + fee_amount
                if total_cost <= cash + 1e-9:
                    break
                candidate_shares -= lot_size

            if candidate_shares > 0:
                trade_shares = candidate_shares
                trade_notional = trade_shares * execution_price
                fee_amount = trade_notional * fee_rate
                slippage_amount = trade_shares * price * slippage_rate
                cash -= trade_notional + fee_amount
                shares += trade_shares
                trade_side = "buy"
            else:
                trade_notional = 0.0
                fee_amount = 0.0

        holdings_value = shares * price
        strategy_capital = cash + holdings_value
        strategy_equity = strategy_capital / initial_capital

        state_rows.append(
            {
                "desired_position": desired_state,
                "cash": cash,
                "shares": shares,
                "holdings_value": holdings_value,
                "strategy_capital": strategy_capital,
                "strategy_equity": strategy_equity,
                "position_for_return": (holdings_value / strategy_capital) if strategy_capital > 0 else 0.0,
                "cash_exposure": (cash / strategy_capital) if strategy_capital > 0 else 1.0,
                "trade_side": trade_side,
                "trade_shares": trade_shares,
                "trade_notional": trade_notional,
                "execution_price": execution_price,
                "order_value": order_value,
                "fee_amount": fee_amount,
                "stamp_duty_amount": stamp_duty_amount,
                "slippage_amount": slippage_amount,
                "starting_cash": starting_cash,
                "starting_shares": starting_shares,
            }
        )

    result = pd.concat([result, pd.DataFrame(state_rows, index=result.index)], axis=1)
    result["gross_strategy_return"] = result["strategy_capital"].pct_change().fillna(
        result["strategy_capital"].iloc[0] / initial_capital - 1.0
    )
    result["trade_turnover"] = result["trade_notional"] / initial_capital
    result["fee_return"] = result["fee_amount"] / initial_capital
    result["stamp_duty_return"] = result["stamp_duty_amount"] / initial_capital
    result["slippage_return"] = result["slippage_amount"] / initial_capital
    result["strategy_return"] = result["strategy_equity"].pct_change().fillna(
        result["strategy_equity"].iloc[0] - 1.0
    )

    strategy_peak = result["strategy_equity"].cummax()
    benchmark_peak = result["benchmark_equity"].cummax()
    result["drawdown"] = result["strategy_equity"] / strategy_peak - 1.0
    result["benchmark_drawdown"] = result["benchmark_equity"] / benchmark_peak - 1.0
    result.attrs["initial_capital"] = float(initial_capital)
    result.attrs["position_size"] = float(position_size)
    result.attrs["fee_rate"] = float(fee_rate)
    result.attrs["stamp_duty_rate"] = float(stamp_duty_rate)
    result.attrs["slippage_rate"] = float(slippage_rate)
    result.attrs["lot_size"] = int(lot_size)
    result.attrs["strategy_params"] = strategy.get_params()
    return result


def summarize_backtest(result: pd.DataFrame) -> dict:
    """Summarize backtest performance and trade statistics."""

    if result.empty:
        raise ValueError("backtest result must not be empty")

    trades = extract_trades(result)

    return {
        "start_date": format_start_or_end(result, first=True),
        "end_date": format_start_or_end(result, first=False),
        "initial_capital": float(result.attrs.get("initial_capital", 1.0)),
        "position_size": float(result.attrs.get("position_size", 1.0)),
        "strategy_params": dict(result.attrs.get("strategy_params", {})),
        "fee_rate": float(result.attrs.get("fee_rate", 0.0)),
        "stamp_duty_rate": float(result.attrs.get("stamp_duty_rate", 0.0)),
        "slippage_rate": float(result.attrs.get("slippage_rate", 0.0)),
        "lot_size": int(result.attrs.get("lot_size", 1)),
        "trading_days": int(len(result)),
        "buy_signals": int((result["signal"] == "buy").sum()),
        "sell_signals": int((result["signal"] == "sell").sum()),
        "executed_buy_trades": int((result["trade_side"] == "buy").sum()),
        "executed_sell_trades": int((result["trade_side"] == "sell").sum()),
        "trade_count": int(len(trades)),
        "active_days": int((result["shares"] > 0).sum()),
        "strategy_total_return": float(result["strategy_equity"].iloc[-1] - 1.0),
        "benchmark_total_return": float(result["benchmark_equity"].iloc[-1] - 1.0),
        "final_strategy_capital": float(result["strategy_capital"].iloc[-1]),
        "final_benchmark_capital": float(result["benchmark_capital"].iloc[-1]),
        "final_shares": int(result["shares"].iloc[-1]),
        "strategy_pnl": float(result["strategy_capital"].iloc[-1] - result.attrs.get("initial_capital", 1.0)),
        "benchmark_pnl": float(result["benchmark_capital"].iloc[-1] - result.attrs.get("initial_capital", 1.0)),
        "total_fees": float(result["fee_amount"].sum()),
        "total_stamp_duty": float(result["stamp_duty_amount"].sum()),
        "total_slippage": float(result["slippage_amount"].sum()),
        "strategy_max_drawdown": float(result["drawdown"].min()),
        "benchmark_max_drawdown": float(result["benchmark_drawdown"].min()),
        "win_rate": float((trades["trade_return"] > 0).mean()) if not trades.empty else 0.0,
        "avg_trade_return": float(trades["trade_return"].mean()) if not trades.empty else 0.0,
    }


def plot_macd_backtest(
    result: pd.DataFrame,
    output_path: str | Path,
    title: str | None = None,
    subtitle: str | None = None,
) -> Path:
    """Render a price/MACD/capital chart with buy and sell markers."""

    return plot_strategy_backtest(
        result,
        output_path,
        title,
        subtitle,
        strategy_panel_renderer=_render_macd_panel,
        parameter_section_builder=_build_macd_parameter_section,
        summary_builder=summarize_backtest,
    )


def _build_macd_parameter_section(summary: dict) -> dict:
    params = summary.get("strategy_params", {})
    fast_period = params.get("fast_period", "-")
    slow_period = params.get("slow_period", "-")
    signal_period = params.get("signal_period", "-")
    zero_axis_filter = params.get("zero_axis_filter", False)
    return {
        "title": "Parameters",
        "lines": [
            ("MACD", f"{fast_period}/{slow_period}/{signal_period}", "#1f2937"),
            ("Zero Filter", str(zero_axis_filter), "#1f2937"),
            ("Capital", f"{summary['initial_capital']:,.0f}", "#1f2937"),
            ("Position", f"{summary['position_size']:.0%}", "#1f2937"),
            ("Lot Size", f"{summary['lot_size']}", "#1f2937"),
            ("Price Column", str(params.get("price_column", "close")), "#1f2937"),
        ],
    }


def _render_macd_panel(axis, result: pd.DataFrame, x_axis: pd.Series) -> None:
    axis.plot(x_axis, result["dif"], label="DIF", color="#0b84a5", linewidth=1.2)
    axis.plot(x_axis, result["dea"], label="DEA", color="#f6c85f", linewidth=1.2)
    axis.bar(x_axis, result["histogram"], label="Histogram", color="#6f4e7c", alpha=0.4)
    axis.axhline(0, color="#444444", linewidth=0.8)
    axis.set_ylabel("MACD")
    axis.legend(loc="upper left")
    axis.grid(alpha=0.25)
