"""SQLAlchemy adapter for the A-share stock-list gateway port."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import DataSource, IngestionBatch, Instrument, QualityCheck


class SqlAlchemyAShareStockListGateway:
    """SQLAlchemy-backed adapter implementing the A-share stock-list gateway port."""

    def __init__(self, session: Session):
        self.session = session

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
    ) -> tuple[int, int]:
        existing_pairs = self.fetch_existing_instrument_pairs(stock_list=stock_list)
        inserted_rows = int(len(stock_list) - len(existing_pairs))
        updated_rows = int(len(existing_pairs))

        existing_by_key = {
            (item.exchange, item.symbol): item
            for item in self.session.scalars(
                select(Instrument).where(Instrument.symbol.in_(stock_list["symbol"].astype(str).tolist()))
            )
        }

        for stock in stock_list.to_dict("records"):
            key = (str(stock["exchange"]), str(stock["symbol"]))
            instrument = existing_by_key.get(key)
            metadata = {"market": stock["market"], "source_dataset": "a_share_stock_list"}
            if instrument is None:
                instrument = Instrument(
                    source_id=source_id,
                    batch_id=batch_id,
                    exchange=key[0],
                    symbol=key[1],
                    instrument_name=str(stock["name"]),
                    instrument_type=instrument_type,
                    currency=currency,
                    status=status,
                    metadata_json=metadata,
                    ingested_at=as_of,
                    as_of=as_of,
                    version=1,
                    raw_uri=raw_uri,
                    created_at=as_of,
                    updated_at=as_of,
                )
                self.session.add(instrument)
                existing_by_key[key] = instrument
                continue

            instrument.source_id = source_id
            instrument.batch_id = batch_id
            instrument.instrument_name = str(stock["name"])
            instrument.instrument_type = instrument_type
            instrument.currency = currency
            instrument.status = status
            instrument.metadata_json = metadata
            instrument.ingested_at = as_of
            instrument.as_of = as_of
            instrument.raw_uri = raw_uri
            instrument.updated_at = as_of

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

    def fetch_existing_instrument_pairs(self, *, stock_list: pd.DataFrame) -> set[tuple[str, str]]:
        symbols = stock_list["symbol"].astype(str).tolist()
        if not symbols:
            return set()

        rows = self.session.execute(
            select(Instrument.exchange, Instrument.symbol).where(Instrument.symbol.in_(symbols))
        ).all()
        return {(str(exchange), str(symbol)) for exchange, symbol in rows}
