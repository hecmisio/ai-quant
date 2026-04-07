"""Shared chart rendering helpers for backtest visualizations."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Sequence

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
from matplotlib.patches import Rectangle
import pandas as pd


SummaryLine = tuple[str, str, str]
SummarySection = dict[str, Sequence[SummaryLine] | str]
REQUIRED_KLINE_VOLUME_COLUMNS = ("open", "high", "low", "close", "volume")


def extract_trades(result: pd.DataFrame) -> pd.DataFrame:
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
                    "entry_value": row_time_or_index(entry),
                    "entry_price": entry_price,
                    "exit_value": row_time_or_index(row),
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
                "entry_value": row_time_or_index(entry),
                "entry_price": entry_price,
                "exit_value": row_time_or_index(last),
                "exit_price": float(last["close"]),
                "shares": int(entry["trade_shares"]),
                "trade_return": float(last["close"]) / entry_price - 1.0,
                "open_trade": True,
            }
        )

    return pd.DataFrame(trades)


def holding_spans(result: pd.DataFrame) -> list[tuple[int, int]]:
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


def annotate_trades(axis, x_axis, result: pd.DataFrame, buy_points: pd.Series, sell_points: pd.Series) -> None:
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


def row_time_or_index(row: pd.Series) -> str | int:
    if "datetime" in row.index and pd.notna(row["datetime"]):
        return str(pd.Timestamp(row["datetime"]).date())
    return int(row.name)


def format_start_or_end(result: pd.DataFrame, first: bool) -> str:
    row = result.iloc[0] if first else result.iloc[-1]
    if "datetime" in result.columns:
        return str(pd.Timestamp(row["datetime"]).date())
    return str(row.name)


def build_common_summary_sections(summary: dict) -> list[SummarySection]:
    return [
        {
            "title": "Performance",
            "lines": [
                (
                    "Return",
                    f"{summary['strategy_total_return']:+.2%}",
                    "#148f3c" if summary["strategy_total_return"] >= 0 else "#c0392b",
                ),
                ("Benchmark", f"{summary['benchmark_total_return']:+.2%}", "#64748b"),
                (
                    "PnL",
                    f"{summary['strategy_pnl']:+,.0f}",
                    "#148f3c" if summary["strategy_pnl"] >= 0 else "#c0392b",
                ),
                ("Max Drawdown", f"{summary['strategy_max_drawdown']:+.2%}", "#c0392b"),
                ("Win Rate", f"{summary['win_rate']:.2%}", "#1f2937"),
                ("Final Shares", f"{summary['final_shares']}", "#1f2937"),
            ],
        },
        {
            "title": "Execution",
            "lines": [
                ("Trades", f"{summary['trade_count']}", "#1f2937"),
                ("Active Days", f"{summary['active_days']}", "#1f2937"),
                ("Fees", f"{summary['total_fees']:,.0f}", "#6b7280"),
                (
                    "Tax / Slip",
                    f"{summary['total_stamp_duty']:,.0f} / {summary['total_slippage']:,.0f}",
                    "#6b7280",
                ),
                ("Fee Rate", f"{summary['fee_rate']:.4%}", "#6b7280"),
                (
                    "Tax / Slip Rate",
                    f"{summary['stamp_duty_rate']:.4%} / {summary['slippage_rate']:.4%}",
                    "#6b7280",
                ),
            ],
        },
    ]


def plot_strategy_backtest(
    result: pd.DataFrame,
    output_path: str | Path,
    title: str | None,
    subtitle: str | None,
    strategy_panel_renderer: Callable[[object, pd.DataFrame, pd.Series], None],
    parameter_section_builder: Callable[[dict], SummarySection],
    summary_builder: Callable[[pd.DataFrame], dict],
) -> Path:
    if result.empty:
        raise ValueError("backtest result must not be empty")

    x_axis = result["datetime"] if "datetime" in result.columns else pd.Series(result.index, index=result.index)
    executed_buy_points = (result["trade_side"] == "buy") & (result["trade_shares"] > 0)
    executed_sell_points = (result["trade_side"] == "sell") & (result["trade_shares"] < 0)

    figure, axes = plt.subplots(3, 1, figsize=(17, 11.6), sharex=True, height_ratios=[3, 2, 2])
    _render_price_panel(axes[0], x_axis, result, executed_buy_points, executed_sell_points)
    strategy_panel_renderer(axes[1], result, x_axis)
    _render_capital_panel(axes[2], x_axis, result)

    if title:
        figure.text(0.06, 0.965, title, ha="left", va="top", fontsize=18, fontweight="bold", color="#0f172a")
    if subtitle:
        figure.text(0.06, 0.935, subtitle, ha="left", va="top", fontsize=11, color="#475569")

    summary = summary_builder(result)
    sections = [parameter_section_builder(summary), *build_common_summary_sections(summary)]
    _add_summary_row(figure, sections)

    figure.tight_layout(rect=(0, 0, 1, 0.73))

    target_path = Path(output_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(target_path, dpi=160, bbox_inches="tight")
    plt.close(figure)
    return target_path


def plot_kline_volume_chart(
    data: pd.DataFrame,
    output_path: str | Path,
    title: str | None = None,
    subtitle: str | None = None,
) -> Path:
    _validate_kline_volume_data(data)

    chart_data = data.reset_index(drop=True).copy()
    x_axis = pd.Series(range(len(chart_data)), index=chart_data.index, dtype=float)
    figure, axes = plt.subplots(2, 1, figsize=(16, 8.8), sharex=True, height_ratios=[3.2, 1.2])
    _render_candlestick_panel(axes[0], x_axis, chart_data)
    _render_volume_panel(axes[1], x_axis, chart_data)
    _format_shared_x_axis(axes[1], chart_data)

    if title:
        figure.text(0.06, 0.965, title, ha="left", va="top", fontsize=18, fontweight="bold", color="#0f172a")
    if subtitle:
        figure.text(0.06, 0.935, subtitle, ha="left", va="top", fontsize=11, color="#475569")

    figure.tight_layout(rect=(0, 0, 1, 0.9))
    target_path = Path(output_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(target_path, dpi=160, bbox_inches="tight")
    plt.close(figure)
    return target_path


def _render_price_panel(axis, x_axis: pd.Series, result: pd.DataFrame, buy_points: pd.Series, sell_points: pd.Series) -> None:
    for start_idx, end_idx in holding_spans(result):
        axis.axvspan(x_axis.iloc[start_idx], x_axis.iloc[end_idx], color="#d4efdf", alpha=0.28, lw=0)

    axis.plot(x_axis, result["close"], label="Close", color="#1f4e79", linewidth=1.4)
    axis.scatter(
        x_axis[buy_points],
        result.loc[buy_points, "close"],
        marker="^",
        color="#148f3c",
        s=70,
        label="Executed Buy",
        zorder=5,
    )
    axis.scatter(
        x_axis[sell_points],
        result.loc[sell_points, "close"],
        marker="v",
        color="#c0392b",
        s=70,
        label="Executed Sell",
        zorder=5,
    )
    annotate_trades(axis, x_axis, result, buy_points, sell_points)
    axis.set_ylabel("Price")
    axis.legend(loc="upper left")
    axis.grid(alpha=0.25)


def _validate_kline_volume_data(data: pd.DataFrame) -> None:
    if data.empty:
        raise ValueError("chart data must not be empty")

    missing_columns = [column for column in REQUIRED_KLINE_VOLUME_COLUMNS if column not in data.columns]
    if missing_columns:
        raise ValueError(f"chart data must include columns: {', '.join(REQUIRED_KLINE_VOLUME_COLUMNS)}")


def _render_candlestick_panel(axis, x_axis: pd.Series, data: pd.DataFrame) -> None:
    candle_width = 0.62

    for idx, row in data.iterrows():
        open_price = float(row["open"])
        high_price = float(row["high"])
        low_price = float(row["low"])
        close_price = float(row["close"])
        x_value = float(x_axis.iloc[idx])
        color = "#c0392b" if close_price >= open_price else "#148f3c"

        axis.vlines(x_value, low_price, high_price, color=color, linewidth=1.0, zorder=2)

        body_bottom = min(open_price, close_price)
        body_height = max(abs(close_price - open_price), 0.01)
        candle = Rectangle(
            (x_value - candle_width / 2, body_bottom),
            candle_width,
            body_height,
            facecolor=color,
            edgecolor=color,
            linewidth=0.8,
            alpha=0.85,
            zorder=3,
        )
        axis.add_patch(candle)

    axis.set_ylabel("Price")
    axis.grid(alpha=0.25)
    axis.set_xlim(-0.8, len(data) - 0.2)


def _render_volume_panel(axis, x_axis: pd.Series, data: pd.DataFrame) -> None:
    colors = ["#c0392b" if float(close_price) >= float(open_price) else "#148f3c" for open_price, close_price in zip(data["open"], data["close"])]
    axis.bar(x_axis.tolist(), data["volume"].tolist(), width=0.62, color=colors, alpha=0.72)
    axis.set_ylabel("Volume")
    axis.set_xlabel("Date" if "datetime" in data.columns else "Row")
    axis.grid(alpha=0.2, axis="y")


def _format_shared_x_axis(axis, data: pd.DataFrame) -> None:
    if data.empty:
        return

    tick_count = min(8, len(data))
    if tick_count <= 1:
        tick_positions = [0]
    else:
        tick_positions = sorted({round(index * (len(data) - 1) / (tick_count - 1)) for index in range(tick_count)})

    axis.set_xticks(tick_positions)
    if "datetime" in data.columns:
        labels = [str(pd.Timestamp(data.iloc[position]["datetime"]).date()) for position in tick_positions]
    else:
        labels = [str(position) for position in tick_positions]
    axis.set_xticklabels(labels, rotation=25, ha="right")


def _render_capital_panel(axis, x_axis: pd.Series, result: pd.DataFrame) -> None:
    axis.plot(x_axis, result["strategy_capital"], label="Strategy Capital", color="#148f3c", linewidth=1.3)
    axis.plot(x_axis, result["benchmark_capital"], label="Benchmark Capital", color="#7f8c8d", linewidth=1.1)
    axis.fill_between(
        x_axis,
        result["strategy_capital"],
        result.attrs.get("initial_capital", 1.0),
        color="#148f3c",
        alpha=0.08,
    )
    axis.set_ylabel("Capital")
    axis.set_xlabel("Date")
    axis.legend(loc="upper left")
    axis.grid(alpha=0.25)


def _add_summary_row(figure, sections: Sequence[SummarySection]) -> None:
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
            str(section["title"]),
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
