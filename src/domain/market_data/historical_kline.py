"""Pure domain logic for provider-backed historical K-line normalization and validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


HISTORICAL_KLINE_COLUMNS = [
    "bar_time",
    "open_price",
    "high_price",
    "low_price",
    "close_price",
    "volume",
    "turnover",
    "trade_count",
]

_BAR_COLUMN_CANDIDATES: dict[str, tuple[str, ...]] = {
    "bar_time": ("bar_time", "datetime", "date", "日期", "时间", "日期时间"),
    "open_price": ("open_price", "open", "开盘"),
    "high_price": ("high_price", "high", "最高"),
    "low_price": ("low_price", "low", "最低"),
    "close_price": ("close_price", "close", "收盘"),
    "volume": ("volume", "成交量"),
    "turnover": ("turnover", "amount", "成交额"),
    "trade_count": ("trade_count", "成交笔数"),
}


@dataclass(frozen=True)
class HistoricalKlineQualityCheck:
    check_name: str
    check_status: str
    severity: str
    details: dict[str, Any]

    @property
    def passed(self) -> bool:
        return self.check_status == "passed"


def normalize_historical_kline_dataframe(raw_data: pd.DataFrame) -> pd.DataFrame:
    resolved: dict[str, str] = {}
    for canonical_name, candidates in _BAR_COLUMN_CANDIDATES.items():
        column = next((candidate for candidate in candidates if candidate in raw_data.columns), None)
        if column is not None:
            resolved[canonical_name] = column

    required = ("bar_time", "open_price", "high_price", "low_price", "close_price", "volume")
    missing_required = [name for name in required if name not in resolved]
    if missing_required:
        raise ValueError(f"historical kline data missing required columns: {missing_required}")

    normalized = pd.DataFrame(
        {
            canonical_name: raw_data[source_name]
            for canonical_name, source_name in resolved.items()
        }
    ).copy()

    normalized["bar_time"] = pd.to_datetime(normalized["bar_time"], errors="coerce", utc=True)
    for column in ("open_price", "high_price", "low_price", "close_price", "volume", "turnover", "trade_count"):
        if column in normalized.columns:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
        else:
            normalized[column] = pd.Series([pd.NA] * len(normalized), index=normalized.index)

    normalized = normalized[HISTORICAL_KLINE_COLUMNS]
    normalized = normalized.sort_values("bar_time").reset_index(drop=True)
    return normalized


def validate_historical_kline_for_ingestion(bars: pd.DataFrame) -> list[HistoricalKlineQualityCheck]:
    required_columns = ("bar_time", "open_price", "high_price", "low_price", "close_price", "volume")
    missing_columns = [column for column in required_columns if column not in bars.columns]
    if missing_columns:
        raise ValueError(f"historical kline data missing required columns: {missing_columns}")

    total_rows = int(len(bars))
    duplicate_bar_times = int(bars["bar_time"].duplicated().sum()) if "bar_time" in bars.columns else 0
    invalid_bar_times = int(bars["bar_time"].isna().sum()) if "bar_time" in bars.columns else total_rows
    invalid_numeric_rows = int(
        bars.loc[:, ["open_price", "high_price", "low_price", "close_price", "volume"]]
        .isna()
        .any(axis=1)
        .sum()
    )
    invalid_price_order_rows = int(
        (
            (bars["low_price"] > bars["open_price"])
            | (bars["low_price"] > bars["close_price"])
            | (bars["low_price"] > bars["high_price"])
            | (bars["high_price"] < bars["open_price"])
            | (bars["high_price"] < bars["close_price"])
            | (bars["high_price"] < bars["low_price"])
        )
        .fillna(False)
        .sum()
    )

    return [
        HistoricalKlineQualityCheck(
            "bars_not_empty",
            "passed" if total_rows > 0 else "failed",
            "info" if total_rows > 0 else "error",
            {"row_count": total_rows},
        ),
        HistoricalKlineQualityCheck(
            "bar_time_present_and_parseable",
            "passed" if invalid_bar_times == 0 else "failed",
            "info" if invalid_bar_times == 0 else "error",
            {"invalid_bar_time_rows": invalid_bar_times},
        ),
        HistoricalKlineQualityCheck(
            "bar_time_unique_within_batch",
            "passed" if duplicate_bar_times == 0 else "failed",
            "info" if duplicate_bar_times == 0 else "error",
            {"duplicate_bar_times": duplicate_bar_times},
        ),
        HistoricalKlineQualityCheck(
            "numeric_ohlcv_fields_valid",
            "passed" if invalid_numeric_rows == 0 else "failed",
            "info" if invalid_numeric_rows == 0 else "error",
            {"invalid_numeric_rows": invalid_numeric_rows},
        ),
        HistoricalKlineQualityCheck(
            "ohlc_price_order_valid",
            "passed" if invalid_price_order_rows == 0 else "failed",
            "info" if invalid_price_order_rows == 0 else "error",
            {"invalid_price_order_rows": invalid_price_order_rows},
        ),
    ]
