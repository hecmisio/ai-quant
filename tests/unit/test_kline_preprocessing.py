"""Pytest tests for K-line CSV normalization."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

from src.data.kline import normalize_kline_csv, normalize_kline_dataframe, read_csv_with_fallback


RAW_KLINE_PATH = Path("data/raw/000681_KLINE.csv")
TEST_OUTPUT_PATH = Path("data/processed/test_000681_KLINE.normalized.csv")


def test_read_csv_with_fallback_detects_gbk_file() -> None:
    frame, encoding = read_csv_with_fallback(RAW_KLINE_PATH)

    assert encoding == "gb18030"
    assert list(frame.columns)[:5] == ["时间", "开", "高", "低", "收"]


def test_normalize_kline_dataframe_maps_columns_and_sorts() -> None:
    frame = pd.DataFrame(
        {
            "时间": ["2025/01/03", "2025/01/02"],
            "开": ["10", "9.8"],
            "高": ["10.5", "10.1"],
            "低": ["9.8", "9.6"],
            "收": ["10.2", "9.9"],
            "成交量": ["1000", "900"],
            "ma1": ["9.9", "9.8"],
        }
    )

    normalized = normalize_kline_dataframe(frame)

    assert list(normalized.columns) == ["datetime", "open", "high", "low", "close", "volume", "ma1"]
    assert normalized["datetime"].is_monotonic_increasing
    assert normalized["close"].dtype.kind in {"f", "i"}


def test_normalize_kline_csv_writes_utf8_output() -> None:
    summary = normalize_kline_csv(RAW_KLINE_PATH, TEST_OUTPUT_PATH)
    normalized = pd.read_csv(TEST_OUTPUT_PATH, encoding="utf-8")

    assert summary["source_encoding"] == "gb18030"
    assert TEST_OUTPUT_PATH.exists()
    assert "datetime" in normalized.columns
    assert "close" in normalized.columns


def test_normalize_script_generates_target_csv() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/normalize_kline_csv.py",
            str(RAW_KLINE_PATH),
            "--output-csv",
            str(TEST_OUTPUT_PATH),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert TEST_OUTPUT_PATH.exists()
    assert "source_encoding=gb18030" in completed.stdout
