"""Tests for historical K-line SQLAlchemy gateway."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.models import Base, Instrument, MarketBar
from src.adapters.outbound.persistence import SqlAlchemyHistoricalKlineGateway


def build_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return Session(engine)


def seed_instrument(session: Session) -> None:
    session.add(
        Instrument(
            source_id=1,
            batch_id=1,
            exchange="SSE",
            symbol="600519",
            instrument_name="Moutai",
            instrument_type="equity",
            currency="CNY",
            status="active",
            metadata_json={},
            ingested_at=datetime(2025, 1, 1, tzinfo=UTC),
            as_of=datetime(2025, 1, 1, tzinfo=UTC),
            version=1,
            raw_uri=None,
            created_at=datetime(2025, 1, 1, tzinfo=UTC),
            updated_at=datetime(2025, 1, 1, tzinfo=UTC),
        )
    )
    session.commit()


def build_bars() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "bar_time": [pd.Timestamp("2025-01-01", tz="UTC"), pd.Timestamp("2025-01-02", tz="UTC")],
            "open_price": [10.0, 11.0],
            "high_price": [10.5, 11.5],
            "low_price": [9.5, 10.5],
            "close_price": [10.2, 11.2],
            "volume": [1000, 1100],
            "turnover": [10000, 11000],
            "trade_count": [10, 11],
        }
    )


def test_sqlalchemy_historical_kline_gateway_resolves_instrument_and_upserts() -> None:
    session = build_session()
    seed_instrument(session)
    gateway = SqlAlchemyHistoricalKlineGateway(session)
    instrument = gateway.get_instrument(exchange="SSE", symbol="600519")

    assert instrument is not None
    source_id = gateway.ensure_source(
        source_code="akshare_historical_kline",
        source_name="AkShare Historical K-line",
        source_type="market",
        description="test",
        metadata={},
        now=datetime(2025, 1, 5, tzinfo=UTC),
    )
    batch_id = gateway.create_batch(source_id=source_id, batch_key="batch-1", raw_uri=None, now=datetime(2025, 1, 5, tzinfo=UTC))
    inserted_rows, updated_rows = gateway.upsert_market_bars(
        bars=build_bars(),
        source_id=source_id,
        batch_id=batch_id,
        instrument_id=int(instrument["instrument_id"]),
        timeframe="1d",
        adjustment_type="none",
        raw_uri=None,
        as_of=datetime(2025, 1, 5, tzinfo=UTC),
        version=1,
    )

    assert inserted_rows == 2
    assert updated_rows == 0

    inserted_rows, updated_rows = gateway.upsert_market_bars(
        bars=build_bars(),
        source_id=source_id,
        batch_id=batch_id,
        instrument_id=int(instrument["instrument_id"]),
        timeframe="1d",
        adjustment_type="none",
        raw_uri=None,
        as_of=datetime(2025, 1, 6, tzinfo=UTC),
        version=1,
    )

    assert inserted_rows == 0
    assert updated_rows == 2
    assert session.query(MarketBar).count() == 2


def test_sqlalchemy_historical_kline_gateway_lists_instruments_with_filters() -> None:
    session = build_session()
    seed_instrument(session)
    session.add(
        Instrument(
            source_id=1,
            batch_id=1,
            exchange="SZSE",
            symbol="000001",
            instrument_name="Ping An Bank",
            instrument_type="equity",
            currency="CNY",
            status="inactive",
            metadata_json={},
            ingested_at=datetime(2025, 1, 1, tzinfo=UTC),
            as_of=datetime(2025, 1, 1, tzinfo=UTC),
            version=1,
            raw_uri=None,
            created_at=datetime(2025, 1, 1, tzinfo=UTC),
            updated_at=datetime(2025, 1, 1, tzinfo=UTC),
        )
    )
    session.commit()

    gateway = SqlAlchemyHistoricalKlineGateway(session)
    active_equities = gateway.list_instruments(instrument_type="equity", status="active")

    assert len(active_equities) == 1
    assert active_equities[0]["symbol"] == "600519"
