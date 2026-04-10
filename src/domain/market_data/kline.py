"""Pure domain logic for K-line dataframe normalization."""

from __future__ import annotations

import pandas as pd


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


def normalize_kline_dataframe(data: pd.DataFrame) -> pd.DataFrame:
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
