"""Application service for historical K-line ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from src.application.ports import HistoricalKlineGateway, HistoricalKlineProvider
from src.domain.market_data import HistoricalKlineQualityCheck, validate_historical_kline_for_ingestion


DEFAULT_SOURCE_CODE = "akshare_historical_kline"
DEFAULT_SOURCE_NAME = "AkShare Historical K-line"
DEFAULT_SOURCE_TYPE = "market"
DEFAULT_VERSION = 1


@dataclass(frozen=True)
class HistoricalKlineIngestionCommand:
    exchange: str
    symbol: str
    timeframe: str = "1d"
    adjustment_type: str = "none"
    start_date: str | None = None
    end_date: str | None = None
    batch_key: str | None = None
    source_code: str = DEFAULT_SOURCE_CODE
    source_name: str = DEFAULT_SOURCE_NAME
    source_type: str = DEFAULT_SOURCE_TYPE
    raw_uri: str | None = None
    as_of: datetime | None = None
    version: int = DEFAULT_VERSION


@dataclass(frozen=True)
class HistoricalKlineIngestionSummary:
    instrument_id: int
    exchange: str
    symbol: str
    timeframe: str
    adjustment_type: str
    source_id: int
    batch_id: int
    batch_key: str
    fetched_rows: int
    inserted_rows: int
    updated_rows: int
    quality_checks: tuple[HistoricalKlineQualityCheck, ...]
    status: str

    @property
    def failed_checks(self) -> tuple[HistoricalKlineQualityCheck, ...]:
        return tuple(check for check in self.quality_checks if not check.passed)


class HistoricalKlineInstrumentNotFoundError(RuntimeError):
    def __init__(self, *, exchange: str, symbol: str):
        self.exchange = exchange
        self.symbol = symbol
        super().__init__(
            f"historical kline ingestion requires an existing instrument in Anne: {exchange}:{symbol}"
        )


class HistoricalKlineIngestionValidationError(RuntimeError):
    def __init__(self, summary: HistoricalKlineIngestionSummary):
        self.summary = summary
        super().__init__(f"historical kline ingestion failed validation for batch {summary.batch_key}")


def make_historical_kline_batch_key(
    *,
    exchange: str,
    symbol: str,
    timeframe: str,
    adjustment_type: str,
    now: datetime | None = None,
) -> str:
    timestamp = (now or datetime.now(UTC)).astimezone(UTC)
    return (
        f"historical_kline_{exchange.lower()}_{symbol}_"
        f"{timeframe}_{adjustment_type}_{timestamp.strftime('%Y%m%dT%H%M%SZ')}"
    )


def ingest_historical_kline(
    gateway: HistoricalKlineGateway,
    *,
    provider: HistoricalKlineProvider,
    exchange: str,
    symbol: str,
    timeframe: str = "1d",
    adjustment_type: str = "none",
    start_date: str | None = None,
    end_date: str | None = None,
    batch_key: str | None = None,
    raw_uri: str | None = None,
    as_of: datetime | None = None,
    version: int = DEFAULT_VERSION,
) -> HistoricalKlineIngestionSummary:
    command = HistoricalKlineIngestionCommand(
        exchange=exchange,
        symbol=symbol,
        timeframe=timeframe,
        adjustment_type=adjustment_type,
        start_date=start_date,
        end_date=end_date,
        batch_key=batch_key,
        raw_uri=raw_uri,
        as_of=as_of,
        version=version,
    )
    return run_historical_kline_ingestion(gateway, provider=provider, command=command)


def run_historical_kline_ingestion(
    gateway: HistoricalKlineGateway,
    *,
    provider: HistoricalKlineProvider,
    command: HistoricalKlineIngestionCommand,
) -> HistoricalKlineIngestionSummary:
    instrument = gateway.get_instrument(exchange=command.exchange, symbol=command.symbol)
    if instrument is None:
        raise HistoricalKlineInstrumentNotFoundError(exchange=command.exchange, symbol=command.symbol)

    bars = provider.fetch_historical_kline(
        symbol=command.symbol,
        exchange=command.exchange,
        timeframe=command.timeframe,
        adjustment_type=command.adjustment_type,
        start_date=command.start_date,
        end_date=command.end_date,
    )
    quality_checks = tuple(validate_historical_kline_for_ingestion(bars))
    batch_time = command.as_of or datetime.now(UTC)
    resolved_batch_key = command.batch_key or make_historical_kline_batch_key(
        exchange=command.exchange,
        symbol=command.symbol,
        timeframe=command.timeframe,
        adjustment_type=command.adjustment_type,
        now=batch_time,
    )

    source_id = gateway.ensure_source(
        source_code=command.source_code,
        source_name=command.source_name,
        source_type=command.source_type,
        description="Normalized historical K-line data sourced from AkShare.",
        metadata={
            "provider": "akshare",
            "dataset": "historical_kline",
            "exchange": command.exchange,
            "symbol": command.symbol,
            "timeframe": command.timeframe,
            "adjustment_type": command.adjustment_type,
        },
        now=batch_time,
    )
    batch_id = gateway.create_batch(
        source_id=source_id,
        batch_key=resolved_batch_key,
        raw_uri=command.raw_uri,
        now=batch_time,
    )
    gateway.record_quality_checks(
        batch_id=batch_id,
        checks=[to_gateway_quality_check_payload(check) for check in quality_checks],
        now=batch_time,
    )

    failed_checks = [check for check in quality_checks if not check.passed]
    if failed_checks:
        gateway.finalize_batch(
            batch_id=batch_id,
            status="failed",
            row_count=0,
            error_count=len(failed_checks),
            notes="Historical K-line validation failed",
            now=batch_time,
        )
        summary = HistoricalKlineIngestionSummary(
            instrument_id=int(instrument["instrument_id"]),
            exchange=command.exchange,
            symbol=command.symbol,
            timeframe=command.timeframe,
            adjustment_type=command.adjustment_type,
            source_id=source_id,
            batch_id=batch_id,
            batch_key=resolved_batch_key,
            fetched_rows=int(len(bars)),
            inserted_rows=0,
            updated_rows=0,
            quality_checks=quality_checks,
            status="failed",
        )
        raise HistoricalKlineIngestionValidationError(summary)

    inserted_rows, updated_rows = gateway.upsert_market_bars(
        bars=bars,
        source_id=source_id,
        batch_id=batch_id,
        instrument_id=int(instrument["instrument_id"]),
        timeframe=command.timeframe,
        adjustment_type=command.adjustment_type,
        raw_uri=command.raw_uri,
        as_of=batch_time,
        version=command.version,
    )
    gateway.finalize_batch(
        batch_id=batch_id,
        status="completed",
        row_count=int(len(bars)),
        error_count=0,
        notes=f"Inserted {inserted_rows} and updated {updated_rows} historical K-line bars",
        now=batch_time,
    )
    return HistoricalKlineIngestionSummary(
        instrument_id=int(instrument["instrument_id"]),
        exchange=command.exchange,
        symbol=command.symbol,
        timeframe=command.timeframe,
        adjustment_type=command.adjustment_type,
        source_id=source_id,
        batch_id=batch_id,
        batch_key=resolved_batch_key,
        fetched_rows=int(len(bars)),
        inserted_rows=inserted_rows,
        updated_rows=updated_rows,
        quality_checks=quality_checks,
        status="completed",
    )


def to_gateway_quality_check_payload(check: HistoricalKlineQualityCheck) -> dict[str, Any]:
    return {
        "check_name": check.check_name,
        "check_status": check.check_status,
        "severity": check.severity,
        "details": check.details,
    }
