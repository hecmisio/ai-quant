"""Ports for the A-share ingestion use case."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

import pandas as pd


class AShareStockListProvider(Protocol):
    """Outbound port for obtaining a normalized A-share stock list."""

    def fetch_stock_list(self, *, include_st: bool = False) -> pd.DataFrame: ...


class AShareStockListGateway(Protocol):
    """Outbound port for persisting A-share stock-list ingestion state."""

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

    def upsert_instruments(
        self,
        *,
        stock_list: pd.DataFrame,
        source_id: int,
        batch_id: int,
        instrument_type: str,
        currency: str,
        status: str,
        raw_uri: str | None,
        as_of: datetime,
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
