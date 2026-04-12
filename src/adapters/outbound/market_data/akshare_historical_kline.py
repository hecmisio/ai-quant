"""AkShare adapter for historical K-line provider port."""

from __future__ import annotations

from typing import Any, Callable

import pandas as pd

from src.domain.market_data import normalize_historical_kline_dataframe


def _load_akshare() -> Any:
    try:
        import akshare as ak  # type: ignore
    except ImportError as exc:
        raise RuntimeError("akshare is required to fetch historical K-line data") from exc
    return ak


def _map_timeframe_to_period(timeframe: str) -> str:
    mapping = {
        "1d": "daily",
        "1w": "weekly",
        "1m": "monthly",
    }
    if timeframe not in mapping:
        raise ValueError(f"unsupported timeframe for AkShare historical K-line provider: {timeframe}")
    return mapping[timeframe]


def _map_adjustment_type(adjustment_type: str) -> str:
    mapping = {
        "none": "",
        "qfq": "qfq",
        "hfq": "hfq",
    }
    if adjustment_type not in mapping:
        raise ValueError(f"unsupported adjustment type for AkShare historical K-line provider: {adjustment_type}")
    return mapping[adjustment_type]


class AkShareHistoricalKlineProvider:
    """Adapter that fetches normalized historical K-line data from AkShare."""

    def __init__(self, fetcher: Callable[..., pd.DataFrame] | None = None):
        self._fetcher = fetcher

    def fetch_historical_kline(
        self,
        *,
        symbol: str,
        exchange: str,
        timeframe: str,
        adjustment_type: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        resolved_fetcher = self._fetcher
        if resolved_fetcher is None:
            ak = _load_akshare()
            resolved_fetcher = ak.stock_zh_a_hist

        raw_data = resolved_fetcher(
            symbol=symbol,
            period=_map_timeframe_to_period(timeframe),
            start_date=(start_date or "").replace("-", ""),
            end_date=(end_date or "").replace("-", ""),
            adjust=_map_adjustment_type(adjustment_type),
        )
        normalized = normalize_historical_kline_dataframe(raw_data)
        normalized["bar_time"] = pd.to_datetime(normalized["bar_time"], utc=True)
        return normalized
