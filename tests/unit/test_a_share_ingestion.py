"""Tests for SQLAlchemy-based A-share stock list ingestion into Anne."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.adapters.outbound.market_data import AkShareAStockListProvider
from src.adapters.outbound.persistence import SqlAlchemyAShareStockListGateway
from db.models import Base, DataSource, IngestionBatch, Instrument, QualityCheck
from db.session import build_anne_conninfo, build_anne_sqlalchemy_url, create_anne_session
from src.application.services.a_share_ingestion import (
    AShareIngestionValidationError,
    ingest_a_share_stock_list,
    validate_stock_list_for_ingestion,
)


@pytest.fixture
def sqlite_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = create_anne_session(engine=engine)
    try:
        yield session
    finally:
        session.close()


def test_validate_stock_list_for_ingestion_detects_structure_issues() -> None:
    stock_list = pd.DataFrame(
        {
            "symbol": ["600519", "600519", ""],
            "name": ["贵州茅台", "贵州茅台", "平安银行"],
            "exchange": ["SSE", "SSE", "SZSE"],
            "market": ["MAIN", "MAIN", "MAIN"],
        }
    )

    checks = validate_stock_list_for_ingestion(stock_list)
    by_name = {check.check_name: check for check in checks}

    assert by_name["stock_list_not_empty"].passed
    assert not by_name["required_fields_not_empty"].passed
    assert not by_name["instrument_business_keys_unique"].passed


def test_ingest_a_share_stock_list_creates_governance_and_instruments(sqlite_session: Session) -> None:
    gateway = SqlAlchemyAShareStockListGateway(sqlite_session)
    provider = AkShareAStockListProvider(
        fetcher=lambda: pd.DataFrame({"code": ["600519", "300750"], "name": ["贵州茅台", "宁德时代"]})
    )

    summary = ingest_a_share_stock_list(
        gateway,
        provider=provider,
        batch_key="test_batch_001",
        raw_uri="akshare://stock_info_a_code_name",
        as_of=datetime(2026, 4, 11, 8, 0, tzinfo=UTC),
    )

    source = sqlite_session.scalar(select(DataSource).where(DataSource.source_code == "akshare_a_share_stock_list"))
    batch = sqlite_session.get(IngestionBatch, summary.batch_id)
    instruments = sqlite_session.scalars(select(Instrument).order_by(Instrument.exchange, Instrument.symbol)).all()
    quality_checks = sqlite_session.scalars(select(QualityCheck).where(QualityCheck.batch_id == summary.batch_id)).all()

    assert summary.status == "completed"
    assert summary.inserted_rows == 2
    assert summary.updated_rows == 0
    assert source is not None
    assert batch is not None and batch.status == "completed"
    assert len(quality_checks) == 3
    assert [(item.exchange, item.symbol, item.instrument_name) for item in instruments] == [
        ("SSE", "600519", "贵州茅台"),
        ("SZSE", "300750", "宁德时代"),
    ]


def test_ingest_a_share_stock_list_is_idempotent_for_existing_identity(sqlite_session: Session) -> None:
    gateway = SqlAlchemyAShareStockListGateway(sqlite_session)
    provider = AkShareAStockListProvider(
        fetcher=lambda: pd.DataFrame({"code": ["600519", "300750"], "name": ["贵州茅台", "宁德时代"]})
    )
    initial_source = DataSource(
        source_code="legacy",
        source_name="Legacy",
        source_type="market",
        description="legacy",
        metadata_json={},
    )
    sqlite_session.add(initial_source)
    sqlite_session.flush()
    sqlite_session.add(
        Instrument(
            source_id=initial_source.id,
            batch_id=None,
            exchange="SSE",
            symbol="600519",
            instrument_name="旧名称",
            instrument_type="equity",
            currency="CNY",
            status="active",
            metadata_json={},
            version=1,
        )
    )
    sqlite_session.commit()

    summary = ingest_a_share_stock_list(gateway, provider=provider, batch_key="test_batch_002")

    instruments = {
        (item.exchange, item.symbol): item
        for item in sqlite_session.scalars(select(Instrument)).all()
    }

    assert summary.inserted_rows == 1
    assert summary.updated_rows == 1
    assert instruments[("SSE", "600519")].instrument_name == "贵州茅台"
    assert instruments[("SZSE", "300750")].instrument_name == "宁德时代"


def test_ingest_a_share_stock_list_marks_failed_batch_on_validation_error(sqlite_session: Session) -> None:
    gateway = SqlAlchemyAShareStockListGateway(sqlite_session)
    provider = AkShareAStockListProvider(
        fetcher=lambda: pd.DataFrame({"code": ["600519", "300750"], "name": ["贵州茅台", ""]})
    )

    with pytest.raises(AShareIngestionValidationError) as exc_info:
        ingest_a_share_stock_list(gateway, provider=provider, batch_key="test_batch_003")

    summary = exc_info.value.summary
    batch = sqlite_session.get(IngestionBatch, summary.batch_id)
    quality_checks = sqlite_session.scalars(select(QualityCheck).where(QualityCheck.batch_id == summary.batch_id)).all()

    assert summary.status == "failed"
    assert summary.inserted_rows == 0
    assert summary.updated_rows == 0
    assert batch is not None and batch.status == "failed"
    assert batch.error_count == 1
    assert len(quality_checks) == 3


def test_build_anne_conninfo_uses_env_defaults_and_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANNE_POSTGRES_DSN", raising=False)
    monkeypatch.setenv("ANNE_POSTGRES_HOST", "db-host")
    monkeypatch.setenv("ANNE_POSTGRES_PORT", "5544")
    monkeypatch.setenv("ANNE_POSTGRES_DB", "anne_test")
    monkeypatch.setenv("ANNE_POSTGRES_USER", "anne_user")
    monkeypatch.setenv("ANNE_POSTGRES_PASSWORD", "secret")

    conninfo = build_anne_conninfo()

    assert conninfo == "host=db-host port=5544 dbname=anne_test user=anne_user password=secret"


def test_build_anne_sqlalchemy_url_uses_postgresql_psycopg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANNE_POSTGRES_DSN", raising=False)
    monkeypatch.setenv("ANNE_POSTGRES_HOST", "db-host")
    monkeypatch.setenv("ANNE_POSTGRES_PORT", "5544")
    monkeypatch.setenv("ANNE_POSTGRES_DB", "anne_test")
    monkeypatch.setenv("ANNE_POSTGRES_USER", "anne_user")
    monkeypatch.setenv("ANNE_POSTGRES_PASSWORD", "secret")

    url = build_anne_sqlalchemy_url()

    assert url == "postgresql+psycopg://anne_user:secret@db-host:5544/anne_test"
