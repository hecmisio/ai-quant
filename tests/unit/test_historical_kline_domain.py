"""Tests for historical K-line normalization and validation."""

from __future__ import annotations

import pandas as pd
import pytest

from src.domain.market_data import (
    normalize_historical_kline_dataframe,
    validate_historical_kline_for_ingestion,
)


def test_normalize_historical_kline_dataframe_maps_akshare_columns() -> None:
    raw = pd.DataFrame(
        {
            "日期": ["2025-01-01", "2025-01-02"],
            "开盘": [10.0, 11.0],
            "最高": [11.0, 12.0],
            "最低": [9.5, 10.5],
            "收盘": [10.5, 11.5],
            "成交量": [1000, 2000],
            "成交额": [10000, 23000],
        }
    )

    result = normalize_historical_kline_dataframe(raw)

    assert result.columns.tolist() == [
        "bar_time",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
        "turnover",
        "trade_count",
    ]
    assert result["bar_time"].dt.tz is not None
    assert result["close_price"].tolist() == [10.5, 11.5]
    assert result["turnover"].tolist() == [10000, 23000]


def test_validate_historical_kline_for_ingestion_reports_failures() -> None:
    bars = pd.DataFrame(
        {
            "bar_time": [pd.Timestamp("2025-01-01", tz="UTC"), pd.Timestamp("2025-01-01", tz="UTC")],
            "open_price": [10.0, 10.0],
            "high_price": [11.0, 9.0],
            "low_price": [9.0, 10.5],
            "close_price": [10.5, 9.5],
            "volume": [1000, None],
            "turnover": [10000, 12000],
            "trade_count": [None, None],
        }
    )

    checks = validate_historical_kline_for_ingestion(bars)
    by_name = {check.check_name: check for check in checks}

    assert by_name["bar_time_unique_within_batch"].check_status == "failed"
    assert by_name["numeric_ohlcv_fields_valid"].check_status == "failed"
    assert by_name["ohlc_price_order_valid"].check_status == "failed"


def test_normalize_historical_kline_dataframe_requires_required_columns() -> None:
    with pytest.raises(ValueError, match="missing required columns"):
        normalize_historical_kline_dataframe(pd.DataFrame({"日期": ["2025-01-01"]}))
