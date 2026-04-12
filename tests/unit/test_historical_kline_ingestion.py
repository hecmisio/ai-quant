"""Tests for historical K-line application workflow."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import pytest

from src.application.services import (
    HistoricalKlineIngestionValidationError,
    HistoricalKlineInstrumentNotFoundError,
    ingest_historical_kline,
)


class StubProvider:
    def __init__(self, bars: pd.DataFrame):
        self.bars = bars

    def fetch_historical_kline(self, **_: object) -> pd.DataFrame:
        return self.bars.copy()


class StubGateway:
    def __init__(self, instrument: dict | None):
        self.instrument = instrument
        self.finalized: dict | None = None
        self.quality_checks: list[dict] = []
        self.upsert_calls: list[dict] = []

    def get_instrument(self, *, exchange: str, symbol: str) -> dict | None:
        return self.instrument

    def ensure_source(self, **_: object) -> int:
        return 11

    def create_batch(self, **_: object) -> int:
        return 22

    def record_quality_checks(self, *, batch_id: int, checks: list[dict], now: datetime) -> None:
        self.quality_checks = checks

    def upsert_market_bars(self, **kwargs: object) -> tuple[int, int]:
        self.upsert_calls.append(kwargs)
        return (2, 1)

    def finalize_batch(self, **kwargs: object) -> None:
        self.finalized = kwargs


def build_valid_bars() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "bar_time": [
                pd.Timestamp("2025-01-01", tz="UTC"),
                pd.Timestamp("2025-01-02", tz="UTC"),
                pd.Timestamp("2025-01-03", tz="UTC"),
            ],
            "open_price": [10.0, 11.0, 12.0],
            "high_price": [10.5, 11.5, 12.5],
            "low_price": [9.8, 10.8, 11.8],
            "close_price": [10.2, 11.2, 12.2],
            "volume": [1000, 1100, 1200],
            "turnover": [10000, 12000, 14000],
            "trade_count": [10, 12, 14],
        }
    )


def test_ingest_historical_kline_completes_successfully() -> None:
    gateway = StubGateway({"instrument_id": 7, "exchange": "SSE", "symbol": "600519"})
    provider = StubProvider(build_valid_bars())

    summary = ingest_historical_kline(
        gateway,
        provider=provider,
        exchange="SSE",
        symbol="600519",
        timeframe="1d",
        adjustment_type="none",
        as_of=datetime(2025, 1, 5, tzinfo=UTC),
    )

    assert summary.status == "completed"
    assert summary.instrument_id == 7
    assert summary.inserted_rows == 2
    assert summary.updated_rows == 1
    assert gateway.finalized is not None
    assert gateway.finalized["status"] == "completed"
    assert len(gateway.upsert_calls) == 1


def test_ingest_historical_kline_fails_when_instrument_missing() -> None:
    gateway = StubGateway(None)
    provider = StubProvider(build_valid_bars())

    with pytest.raises(HistoricalKlineInstrumentNotFoundError, match="requires an existing instrument"):
        ingest_historical_kline(
            gateway,
            provider=provider,
            exchange="SSE",
            symbol="600519",
        )


def test_ingest_historical_kline_records_failed_validation() -> None:
    invalid_bars = build_valid_bars()
    invalid_bars.loc[1, "volume"] = None

    gateway = StubGateway({"instrument_id": 7, "exchange": "SSE", "symbol": "600519"})
    provider = StubProvider(invalid_bars)

    with pytest.raises(HistoricalKlineIngestionValidationError) as exc_info:
        ingest_historical_kline(
            gateway,
            provider=provider,
            exchange="SSE",
            symbol="600519",
        )

    assert exc_info.value.summary.status == "failed"
    assert gateway.finalized is not None
    assert gateway.finalized["status"] == "failed"
    assert gateway.upsert_calls == []
