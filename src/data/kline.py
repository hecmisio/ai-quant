"""Utilities for converting raw K-line CSV files into normalized UTF-8 datasets."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ENCODING_CANDIDATES = ("utf-8", "utf-8-sig", "gb18030", "gbk")

STANDARD_COLUMN_MAP = {
    "时间": "datetime",
    "日期": "datetime",
    "开": "open",
    "开盘": "open",
    "高": "high",
    "最高": "high",
    "低": "low",
    "最低": "low",
    "收": "close",
    "收盘": "close",
    "成交量": "volume",
    "成交额": "turnover",
    "涨跌": "change",
    "涨跌百分比": "change_pct",
    "振幅": "amplitude",
    "持仓量": "open_interest",
}


def read_csv_with_fallback(path: str | Path, encodings: tuple[str, ...] = ENCODING_CANDIDATES) -> tuple[pd.DataFrame, str]:
    """Read CSV using the first encoding that succeeds."""

    csv_path = Path(path)
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            return pd.read_csv(csv_path, encoding=encoding), encoding
        except UnicodeDecodeError as exc:
            last_error = exc
    raise ValueError(f"unable to decode CSV file: {csv_path}") from last_error


def normalize_kline_dataframe(data: pd.DataFrame) -> pd.DataFrame:
    """Rename K-line columns to ASCII-friendly names and normalize dtypes."""

    renamed = data.rename(columns={column: STANDARD_COLUMN_MAP.get(column, column) for column in data.columns}).copy()

    if "close" not in renamed.columns:
        raise ValueError("input data must include a close column")

    if "datetime" in renamed.columns:
        renamed["datetime"] = pd.to_datetime(renamed["datetime"])

    numeric_candidates = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "turnover",
        "change",
        "change_pct",
        "amplitude",
        "open_interest",
    ]
    for column in numeric_candidates:
        if column in renamed.columns:
            renamed[column] = pd.to_numeric(renamed[column], errors="coerce")

    ma_columns = [column for column in renamed.columns if str(column).lower().startswith("ma")]
    for column in ma_columns:
        renamed[column] = pd.to_numeric(renamed[column], errors="coerce")

    if "datetime" in renamed.columns:
        renamed = renamed.sort_values("datetime").reset_index(drop=True)
    else:
        renamed = renamed.reset_index(drop=True)
    return renamed


def normalize_kline_csv(input_path: str | Path, output_path: str | Path) -> dict:
    """Convert raw K-line CSV into UTF-8 encoded normalized CSV."""

    raw_data, source_encoding = read_csv_with_fallback(input_path)
    normalized = normalize_kline_dataframe(raw_data)

    target_path = Path(output_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_csv(target_path, index=False, encoding="utf-8")

    return {
        "input_path": str(Path(input_path)),
        "output_path": str(target_path),
        "source_encoding": source_encoding,
        "rows": int(len(normalized)),
        "columns": list(normalized.columns),
    }
