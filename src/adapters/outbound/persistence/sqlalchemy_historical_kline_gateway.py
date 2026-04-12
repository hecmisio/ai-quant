"""SQLAlchemy adapter for historical K-line ingestion gateway port."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import DataSource, IngestionBatch, Instrument, MarketBar, QualityCheck


class SqlAlchemyHistoricalKlineGateway:
    """SQLAlchemy-backed adapter implementing the historical K-line gateway port."""

    def __init__(self, session: Session):
        self.session = session

    def list_instruments(
        self,
        *,
        instrument_type: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        query = select(Instrument)
        if instrument_type is not None:
            query = query.where(Instrument.instrument_type == instrument_type)
        if status is not None:
            query = query.where(Instrument.status == status)

        instruments = self.session.scalars(query.order_by(Instrument.exchange, Instrument.symbol)).all()
        return [
            {
                "instrument_id": int(instrument.id),
                "exchange": instrument.exchange,
                "symbol": instrument.symbol,
                "instrument_name": instrument.instrument_name,
                "instrument_type": instrument.instrument_type,
                "status": instrument.status,
            }
            for instrument in instruments
        ]

    def get_instrument(self, *, exchange: str, symbol: str) -> dict[str, Any] | None:
        instrument = self.session.scalar(
            select(Instrument).where(Instrument.exchange == exchange, Instrument.symbol == symbol)
        )
        if instrument is None:
            return None
        return {
            "instrument_id": int(instrument.id),
            "exchange": instrument.exchange,
            "symbol": instrument.symbol,
            "instrument_name": instrument.instrument_name,
        }

    def ensure_source(
        self,
        *,
        source_code: str,
        source_name: str,
        source_type: str,
        description: str,
        metadata: dict[str, Any],
        now: datetime,
    ) -> int:
        source = self.session.scalar(select(DataSource).where(DataSource.source_code == source_code))
        if source is None:
            source = DataSource(
                source_code=source_code,
                source_name=source_name,
                source_type=source_type,
                description=description,
                metadata_json=metadata,
                created_at=now,
                updated_at=now,
            )
            self.session.add(source)
        else:
            source.source_name = source_name
            source.source_type = source_type
            source.description = description
            source.metadata_json = metadata
            source.updated_at = now
        self.session.flush()
        return int(source.id)

    def create_batch(self, *, source_id: int, batch_key: str, raw_uri: str | None, now: datetime) -> int:
        batch = IngestionBatch(
            source_id=source_id,
            batch_key=batch_key,
            status="pending",
            started_at=now,
            raw_uri=raw_uri,
            error_count=0,
            created_at=now,
            updated_at=now,
        )
        self.session.add(batch)
        self.session.flush()
        return int(batch.id)

    def record_quality_checks(self, *, batch_id: int, checks: list[dict[str, Any]], now: datetime) -> None:
        self.session.add_all(
            [
                QualityCheck(
                    batch_id=batch_id,
                    check_name=str(check["check_name"]),
                    check_status=str(check["check_status"]),
                    severity=str(check["severity"]),
                    details=dict(check["details"]),
                    checked_at=now,
                    created_at=now,
                )
                for check in checks
            ]
        )
        self.session.flush()

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
    ) -> tuple[int, int]:
        existing_rows = {
            _normalize_bar_time_key(item.bar_time): item
            for item in self.session.scalars(
                select(MarketBar).where(
                    MarketBar.instrument_id == instrument_id,
                    MarketBar.timeframe == timeframe,
                    MarketBar.adjustment_type == adjustment_type,
                    MarketBar.version == version,
                    MarketBar.bar_time.in_(bars["bar_time"].tolist()),
                )
            )
        }

        inserted_rows = 0
        updated_rows = 0
        for row in bars.to_dict("records"):
            bar_time = pd.Timestamp(row["bar_time"]).to_pydatetime()
            market_bar = existing_rows.get(_normalize_bar_time_key(row["bar_time"]))
            if market_bar is None:
                market_bar = MarketBar(
                    source_id=source_id,
                    batch_id=batch_id,
                    instrument_id=instrument_id,
                    timeframe=timeframe,
                    adjustment_type=adjustment_type,
                    bar_time=bar_time,
                    open_price=_float_or_none(row["open_price"]),
                    high_price=_float_or_none(row["high_price"]),
                    low_price=_float_or_none(row["low_price"]),
                    close_price=_float_or_none(row["close_price"]),
                    volume=_float_or_none(row["volume"]),
                    turnover=_float_or_none(row.get("turnover")),
                    trade_count=_int_or_none(row.get("trade_count")),
                    ingested_at=as_of,
                    as_of=as_of,
                    version=version,
                    raw_uri=raw_uri,
                    created_at=as_of,
                )
                self.session.add(market_bar)
                inserted_rows += 1
                continue

            market_bar.source_id = source_id
            market_bar.batch_id = batch_id
            market_bar.open_price = _float_or_none(row["open_price"])
            market_bar.high_price = _float_or_none(row["high_price"])
            market_bar.low_price = _float_or_none(row["low_price"])
            market_bar.close_price = _float_or_none(row["close_price"])
            market_bar.volume = _float_or_none(row["volume"])
            market_bar.turnover = _float_or_none(row.get("turnover"))
            market_bar.trade_count = _int_or_none(row.get("trade_count"))
            market_bar.ingested_at = as_of
            market_bar.as_of = as_of
            market_bar.raw_uri = raw_uri
            updated_rows += 1

        self.session.flush()
        return inserted_rows, updated_rows

    def finalize_batch(
        self,
        *,
        batch_id: int,
        status: str,
        row_count: int,
        error_count: int,
        notes: str,
        now: datetime,
    ) -> None:
        batch = self.session.get(IngestionBatch, batch_id)
        if batch is None:
            raise RuntimeError(f"missing ingestion batch {batch_id}")

        batch.status = status
        batch.row_count = row_count
        batch.error_count = error_count
        batch.notes = notes
        batch.completed_at = now
        batch.updated_at = now
        self.session.commit()


def _float_or_none(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return float(value)


def _int_or_none(value: Any) -> int | None:
    if pd.isna(value):
        return None
    return int(value)


def _normalize_bar_time_key(value: Any) -> str:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp.isoformat()
