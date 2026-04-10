"""Filesystem adapter for K-line CSV reads and writes."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.domain.market_data.kline import normalize_kline_dataframe


ENCODING_CANDIDATES = ("utf-8", "utf-8-sig", "gb18030", "gbk")


def read_csv_with_fallback(path: str | Path, encodings: tuple[str, ...] = ENCODING_CANDIDATES) -> tuple[pd.DataFrame, str]:
    csv_path = Path(path)
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            return pd.read_csv(csv_path, encoding=encoding), encoding
        except UnicodeDecodeError as exc:
            last_error = exc
    raise ValueError(f"unable to decode CSV file: {csv_path}") from last_error


def normalize_kline_csv(input_path: str | Path, output_path: str | Path) -> dict:
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
