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

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import pandas as pd

from src.strategies.trend import MACDStrategy


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

    trades = _extract_trades(result)

    summary = {
        "start_date": _format_start_or_end(result, first=True),
        "end_date": _format_start_or_end(result, first=False),
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
    return summary


def plot_macd_backtest(
    result: pd.DataFrame,
    output_path: str | Path,
    title: str | None = None,
    subtitle: str | None = None,
) -> Path:
    """Render a price/MACD/capital chart with buy and sell markers."""

    if result.empty:
        raise ValueError("backtest result must not be empty")

    x_axis = result["datetime"] if "datetime" in result.columns else pd.Series(result.index, index=result.index)
    executed_buy_points = (result["trade_side"] == "buy") & (result["trade_shares"] > 0)
    executed_sell_points = (result["trade_side"] == "sell") & (result["trade_shares"] < 0)

    figure, axes = plt.subplots(3, 1, figsize=(17, 11.6), sharex=True, height_ratios=[3, 2, 2])

    for start_idx, end_idx in _holding_spans(result):
        axes[0].axvspan(x_axis.iloc[start_idx], x_axis.iloc[end_idx], color="#d4efdf", alpha=0.28, lw=0)

    axes[0].plot(x_axis, result["close"], label="Close", color="#1f4e79", linewidth=1.4)
    axes[0].scatter(
        x_axis[executed_buy_points],
        result.loc[executed_buy_points, "close"],
        marker="^",
        color="#148f3c",
        s=70,
        label="Executed Buy",
        zorder=5,
    )
    axes[0].scatter(
        x_axis[executed_sell_points],
        result.loc[executed_sell_points, "close"],
        marker="v",
        color="#c0392b",
        s=70,
        label="Executed Sell",
        zorder=5,
    )
    _annotate_trades(axes[0], x_axis, result, executed_buy_points, executed_sell_points)
    axes[0].set_ylabel("Price")
    axes[0].legend(loc="upper left")
    axes[0].grid(alpha=0.25)
    if title:
        figure.text(0.06, 0.965, title, ha="left", va="top", fontsize=18, fontweight="bold", color="#0f172a")
    if subtitle:
        figure.text(0.06, 0.935, subtitle, ha="left", va="top", fontsize=11, color="#475569")

    axes[1].plot(x_axis, result["dif"], label="DIF", color="#0b84a5", linewidth=1.2)
    axes[1].plot(x_axis, result["dea"], label="DEA", color="#f6c85f", linewidth=1.2)
    axes[1].bar(x_axis, result["histogram"], label="Histogram", color="#6f4e7c", alpha=0.4)
    axes[1].axhline(0, color="#444444", linewidth=0.8)
    axes[1].set_ylabel("MACD")
    axes[1].legend(loc="upper left")
    axes[1].grid(alpha=0.25)

    axes[2].plot(x_axis, result["strategy_capital"], label="Strategy Capital", color="#148f3c", linewidth=1.3)
    axes[2].plot(x_axis, result["benchmark_capital"], label="Benchmark Capital", color="#7f8c8d", linewidth=1.1)
    axes[2].fill_between(
        x_axis,
        result["strategy_capital"],
        result.attrs.get("initial_capital", 1.0),
        color="#148f3c",
        alpha=0.08,
    )
    summary = summarize_backtest(result)
    _add_summary_row(figure, summary)
    axes[2].set_ylabel("Capital")
    axes[2].set_xlabel("Date")
    axes[2].legend(loc="upper left")
    axes[2].grid(alpha=0.25)

    figure.tight_layout(rect=(0, 0, 1, 0.73))

    target_path = Path(output_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(target_path, dpi=160, bbox_inches="tight")
    plt.close(figure)
    return target_path


def _extract_trades(result: pd.DataFrame) -> pd.DataFrame:
    trades: list[dict] = []
    entry = None

    for _, row in result.iterrows():
        if row["trade_side"] == "buy" and row["trade_shares"] > 0:
            entry = row.copy()
        elif row["trade_side"] == "sell" and entry is not None:
            entry_price = float(entry["execution_price"])
            exit_price = float(row["execution_price"])
            trades.append(
                {
                    "entry_value": _row_time_or_index(entry),
                    "entry_price": entry_price,
                    "exit_value": _row_time_or_index(row),
                    "exit_price": exit_price,
                    "shares": int(entry["trade_shares"]),
                    "trade_return": exit_price / entry_price - 1.0,
                }
            )
            entry = None

    if entry is not None:
        last = result.iloc[-1]
        entry_price = float(entry["execution_price"])
        trades.append(
            {
                "entry_value": _row_time_or_index(entry),
                "entry_price": entry_price,
                "exit_value": _row_time_or_index(last),
                "exit_price": float(last["close"]),
                "shares": int(entry["trade_shares"]),
                "trade_return": float(last["close"]) / entry_price - 1.0,
                "open_trade": True,
            }
        )

    return pd.DataFrame(trades)


def _holding_spans(result: pd.DataFrame) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    in_span = False
    start_idx = 0

    for idx, shares in enumerate(result["shares"].tolist()):
        if shares > 0 and not in_span:
            start_idx = idx
            in_span = True
        elif shares <= 0 and in_span:
            spans.append((start_idx, idx))
            in_span = False

    if in_span:
        spans.append((start_idx, len(result) - 1))
    return spans


def _annotate_trades(axis, x_axis, result: pd.DataFrame, buy_points: pd.Series, sell_points: pd.Series) -> None:
    active_entry = None

    for idx, row in result.iterrows():
        is_buy = bool(buy_points.loc[idx])
        is_sell = bool(sell_points.loc[idx])

        if is_buy:
            active_entry = row
            axis.annotate(
                f"+{int(row['trade_shares'])} @ {row['execution_price']:.2f}",
                (x_axis.iloc[idx], row["close"]),
                textcoords="offset points",
                xytext=(8, 10),
                fontsize=8,
                color="#148f3c",
                bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "#148f3c", "alpha": 0.8},
            )

        elif is_sell:
            pnl_text = ""
            if active_entry is not None and float(active_entry["execution_price"]) > 0:
                trade_return = float(row["execution_price"]) / float(active_entry["execution_price"]) - 1.0
                pnl_text = f" ({trade_return:+.2%})"
            axis.annotate(
                f"{int(row['trade_shares'])} @ {row['execution_price']:.2f}{pnl_text}",
                (x_axis.iloc[idx], row["close"]),
                textcoords="offset points",
                xytext=(8, -18),
                fontsize=8,
                color="#c0392b",
                bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "#c0392b", "alpha": 0.8},
            )
            active_entry = None

    if active_entry is not None:
        last_idx = result.index[-1]
        last_row = result.iloc[-1]
        if float(active_entry["execution_price"]) > 0:
            open_return = float(last_row["close"]) / float(active_entry["execution_price"]) - 1.0
            axis.annotate(
                f"Open {open_return:+.2%}",
                (x_axis.iloc[last_idx], last_row["close"]),
                textcoords="offset points",
                xytext=(8, -18),
                fontsize=8,
                color="#7d6608",
                bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "#b7950b", "alpha": 0.8},
            )


def _row_time_or_index(row: pd.Series) -> str | int:
    if "datetime" in row.index and pd.notna(row["datetime"]):
        return str(pd.Timestamp(row["datetime"]).date())
    return int(row.name)


def _format_start_or_end(result: pd.DataFrame, first: bool) -> str:
    row = result.iloc[0] if first else result.iloc[-1]
    if "datetime" in result.columns:
        return str(pd.Timestamp(row["datetime"]).date())
    return str(row.name)


def _add_summary_row(figure, summary: dict) -> None:
    params = summary.get("strategy_params", {})
    fast_period = params.get("fast_period", "-")
    slow_period = params.get("slow_period", "-")
    signal_period = params.get("signal_period", "-")
    zero_axis_filter = params.get("zero_axis_filter", False)

    sections = [
        {
            "title": "Parameters（参数）",
            "lines": [
                ("MACD", f"{fast_period}/{slow_period}/{signal_period}", "#1f2937"),
                ("Zero Filter（零轴过滤）", str(zero_axis_filter), "#1f2937"),
                ("Capital（本金）", f"{summary['initial_capital']:,.0f}", "#1f2937"),
                ("Position（仓位）", f"{summary['position_size']:.0%}", "#1f2937"),
                ("Lot Size（每手股数）", f"{summary['lot_size']}", "#1f2937"),
                ("Price Column", str(params.get("price_column", "close")), "#1f2937"),
            ],
        },
        {
            "title": "Performance（表现）",
            "lines": [
                (
                    "Return（收益）",
                    f"{summary['strategy_total_return']:+.2%}",
                    "#148f3c" if summary["strategy_total_return"] >= 0 else "#c0392b",
                ),
                ("Benchmark（基准）", f"{summary['benchmark_total_return']:+.2%}", "#64748b"),
                (
                    "PnL（盈亏）",
                    f"{summary['strategy_pnl']:+,.0f}",
                    "#148f3c" if summary["strategy_pnl"] >= 0 else "#c0392b",
                ),
                ("Max Drawdown（最大回撤）", f"{summary['strategy_max_drawdown']:+.2%}", "#c0392b"),
                ("Win Rate（胜率）", f"{summary['win_rate']:.2%}", "#1f2937"),
                ("Final Shares（期末持股）", f"{summary['final_shares']}", "#1f2937"),
            ],
        },
        {
            "title": "Execution（交易执行）",
            "lines": [
                ("Trades（交易笔数）", f"{summary['trade_count']}", "#1f2937"),
                ("Active Days（持仓天数）", f"{summary['active_days']}", "#1f2937"),
                ("Fees（手续费）", f"{summary['total_fees']:,.0f}", "#6b7280"),
                ("Tax / Slip", f"{summary['total_stamp_duty']:,.0f} / {summary['total_slippage']:,.0f}", "#6b7280"),
                ("Fee Rate", f"{summary['fee_rate']:.4%}", "#6b7280"),
                ("Tax / Slip Rate", f"{summary['stamp_duty_rate']:.4%} / {summary['slippage_rate']:.4%}", "#6b7280"),
            ],
        },
    ]

    lefts = [0.06, 0.365, 0.67]
    panel_y = 0.745
    panel_w = 0.27
    panel_h = 0.150
    title_offset = 0.132
    first_line_offset = 0.106
    line_gap = 0.0185
    label_x_offset = 0.016
    value_x_offset = 0.170

    for left, section in zip(lefts, sections):
        panel = FancyBboxPatch(
            (left, panel_y),
            panel_w,
            panel_h,
            transform=figure.transFigure,
            boxstyle="round,pad=0.010",
            fc="#fcfcf8",
            ec="#cbd5e1",
            linewidth=1.0,
            zorder=2,
        )
        figure.patches.append(panel)
        figure.text(
            left + label_x_offset,
            panel_y + title_offset,
            section["title"],
            ha="left",
            va="top",
            fontsize=11,
            fontweight="bold",
            color="#334155",
        )
        line_y = panel_y + first_line_offset
        for label, value, color in section["lines"]:
            figure.text(
                left + label_x_offset,
                line_y,
                label,
                ha="left",
                va="top",
                fontsize=8.9,
                color="#64748b",
            )
            figure.text(
                left + value_x_offset,
                line_y,
                value,
                ha="left",
                va="top",
                fontsize=9.2,
                color=color,
                fontweight="bold",
            )
            line_y -= line_gap
