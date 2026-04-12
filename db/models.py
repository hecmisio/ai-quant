"""SQLAlchemy ORM models for Anne PostgreSQL."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for Anne ORM models."""


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_code: Mapped[str] = mapped_column(Text, unique=True)
    source_name: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IngestionBatch(Base):
    __tablename__ = "ingestion_batches"
    __table_args__ = (UniqueConstraint("source_id", "batch_key", name="uq_ingestion_batches_source_batch_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(Integer)
    batch_key: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class QualityCheck(Base):
    __tablename__ = "quality_checks"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(Integer)
    check_name: Mapped[str] = mapped_column(Text)
    check_status: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(Text)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Instrument(Base):
    __tablename__ = "instruments"
    __table_args__ = (UniqueConstraint("exchange", "symbol", name="uq_instruments_exchange_symbol"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(Integer)
    batch_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exchange: Mapped[str] = mapped_column(Text)
    symbol: Mapped[str] = mapped_column(Text)
    instrument_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    instrument_type: Mapped[str] = mapped_column(Text)
    currency: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    ingested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    raw_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MarketBar(Base):
    __tablename__ = "market_bars"
    __table_args__ = (
        UniqueConstraint(
            "instrument_id",
            "bar_time",
            "timeframe",
            "adjustment_type",
            "version",
            name="uq_market_bars_business_key",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(Integer)
    batch_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    instrument_id: Mapped[int] = mapped_column(Integer)
    timeframe: Mapped[str] = mapped_column(Text)
    adjustment_type: Mapped[str] = mapped_column(Text, default="none")
    bar_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    open_price: Mapped[float | None] = mapped_column(Numeric(20, 6), nullable=True)
    high_price: Mapped[float | None] = mapped_column(Numeric(20, 6), nullable=True)
    low_price: Mapped[float | None] = mapped_column(Numeric(20, 6), nullable=True)
    close_price: Mapped[float | None] = mapped_column(Numeric(20, 6), nullable=True)
    volume: Mapped[float | None] = mapped_column(Numeric(24, 6), nullable=True)
    turnover: Mapped[float | None] = mapped_column(Numeric(24, 6), nullable=True)
    trade_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ingested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    raw_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
