"""Outbound filesystem adapters."""

from .kline_csv import ENCODING_CANDIDATES, normalize_kline_csv, read_csv_with_fallback

__all__ = ["ENCODING_CANDIDATES", "normalize_kline_csv", "read_csv_with_fallback"]
