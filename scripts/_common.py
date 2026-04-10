"""Shared helpers for strategy runner and backtest scripts."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.adapters.outbound.filesystem import read_csv_with_fallback
from src.domain.market_data import normalize_kline_dataframe


def load_price_data(input_csv: str) -> pd.DataFrame:
    raw_data, _ = read_csv_with_fallback(input_csv)
    return normalize_kline_dataframe(raw_data)


def filter_by_date(data: pd.DataFrame, start_date: str | None, end_date: str | None) -> pd.DataFrame:
    if "datetime" not in data.columns:
        return data

    filtered = data.copy()
    if start_date:
        filtered = filtered[filtered["datetime"] >= start_date]
    if end_date:
        filtered = filtered[filtered["datetime"] <= end_date]
    return filtered.reset_index(drop=True)


def default_report_path(input_csv: str, suffix: str) -> Path:
    return ROOT / "outputs" / "reports" / f"{Path(input_csv).stem}.{suffix}"


def strategy_symbol(input_csv: str) -> str:
    return Path(input_csv).stem.replace("_KLINE", "")


def write_output_csv(data: pd.DataFrame, output_csv: str | Path) -> Path:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output_path, index=False)
    return output_path
