"""Ports for historical K-line ingestion workflows."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

import pandas as pd


class HistoricalKlineProvider(Protocol):
    """Outbound port for obtaining normalized historical K-line data."""

    def fetch_historical_kline(
        self,
        *,
        symbol: str,
        exchange: str,
        timeframe: str,
        adjustment_type: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame: ...


class HistoricalKlineGateway(Protocol):
    """Outbound port for persisting historical K-line ingestion state."""

    def list_instruments(
        self,
        *,
        instrument_type: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]: ...

    def get_instrument(
        self,
        *,
        exchange: str,
        symbol: str,
    ) -> dict[str, Any] | None: ...

    def ensure_source(
        self,
        *,
        source_code: str,
        source_name: str,
        source_type: str,
        description: str,
        metadata: dict[str, Any],
        now: datetime,
    ) -> int: ...

    def create_batch(self, *, source_id: int, batch_key: str, raw_uri: str | None, now: datetime) -> int: ...

    def record_quality_checks(self, *, batch_id: int, checks: list[dict[str, Any]], now: datetime) -> None: ...

    def upsert_market_bars(
        self,
        *,
        bars: pd.DataFrame,
        source_id: int,
        batch_id: int,
        instrument_id: int,
        timeframe: str,
        adjustment_type: str,
        raw_uri: str | None,
        as_of: datetime,
        version: int,
    ) -> tuple[int, int]: ...

    def finalize_batch(
        self,
        *,
        batch_id: int,
        status: str,
        row_count: int,
        error_count: int,
        notes: str,
        now: datetime,
    ) -> None: ...
