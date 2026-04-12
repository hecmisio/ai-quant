"""Tests for historical K-line CLI and provider adapter behavior."""

from __future__ import annotations

from argparse import Namespace
import sys
from pathlib import Path

import pandas as pd
import pytest

from src.adapters.inbound.cli import historical_kline_cli
from src.adapters.outbound.market_data import AkShareHistoricalKlineProvider
from src.application.services import HistoricalKlineIngestionSummary


def test_akshare_historical_kline_provider_normalizes_output() -> None:
    def fake_fetcher(**_: object) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "日期": ["2025-01-01"],
                "开盘": [10.0],
                "最高": [10.5],
                "最低": [9.5],
                "收盘": [10.2],
                "成交量": [1000],
                "成交额": [10000],
            }
        )

    provider = AkShareHistoricalKlineProvider(fetcher=fake_fetcher)
    result = provider.fetch_historical_kline(
        symbol="600519",
        exchange="SSE",
        timeframe="1d",
        adjustment_type="none",
    )

    assert result.loc[0, "close_price"] == 10.2
    assert "bar_time" in result.columns


def test_historical_kline_cli_prints_summary(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    class DummySession:
        def close(self) -> None:
            pass

    summary = HistoricalKlineIngestionSummary(
        instrument_id=7,
        exchange="SSE",
        symbol="600519",
        timeframe="1d",
        adjustment_type="none",
        source_id=11,
        batch_id=22,
        batch_key="batch-1",
        fetched_rows=3,
        inserted_rows=2,
        updated_rows=1,
        quality_checks=tuple(),
        status="completed",
    )

    monkeypatch.setattr(historical_kline_cli, "create_anne_session", lambda: DummySession())
    monkeypatch.setattr(historical_kline_cli, "SqlAlchemyHistoricalKlineGateway", lambda session: object())
    monkeypatch.setattr(historical_kline_cli, "AkShareHistoricalKlineProvider", lambda: object())
    monkeypatch.setattr(historical_kline_cli, "ingest_historical_kline", lambda *args, **kwargs: summary)
    monkeypatch.setattr(
        sys,
        "argv",
        ["ingest_historical_kline.py", "--exchange", "SSE", "--symbol", "600519"],
    )

    historical_kline_cli.run_ingest_command()
    output = capsys.readouterr().out

    assert "Status: completed" in output
    assert "Symbol: 600519" in output


def test_historical_kline_cli_runs_bulk_mode(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    class DummySession:
        def close(self) -> None:
            pass

    class DummyGateway:
        def __init__(self, session: object):
            self.session = session

        def list_instruments(self, *, instrument_type: str | None = None, status: str | None = None) -> list[dict]:
            return [
                {"exchange": "SSE", "symbol": "600519"},
                {"exchange": "SZSE", "symbol": "000001"},
            ]

    summary = HistoricalKlineIngestionSummary(
        instrument_id=7,
        exchange="SSE",
        symbol="600519",
        timeframe="1d",
        adjustment_type="none",
        source_id=11,
        batch_id=22,
        batch_key="batch-1",
        fetched_rows=3,
        inserted_rows=2,
        updated_rows=1,
        quality_checks=tuple(),
        status="completed",
    )

    monkeypatch.setattr(historical_kline_cli, "create_anne_engine", lambda: object())
    monkeypatch.setattr(historical_kline_cli, "create_anne_session", lambda engine=None: DummySession())
    monkeypatch.setattr(historical_kline_cli, "SqlAlchemyHistoricalKlineGateway", DummyGateway)
    monkeypatch.setattr(
        historical_kline_cli,
        "_ingest_one_instrument",
        lambda **kwargs: historical_kline_cli.BulkHistoricalKlineResult(
            exchange=kwargs["exchange"],
            symbol=kwargs["symbol"],
            success=True,
            summary=summary,
        ),
    )

    args = Namespace(
        instrument_type="equity",
        instrument_status="active",
        timeframe="1d",
        adjustment_type="none",
        start_date=None,
        end_date=None,
        max_workers=2,
    )
    historical_kline_cli.run_bulk_ingest_command(args=args, raw_uri="script")
    output = capsys.readouterr().out

    assert "Bulk Historical K-line Ingestion Summary:" in output
    assert "Total Instruments: 2" in output
    assert "Succeeded: 2" in output


def test_historical_kline_script_delegates_to_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib.util

    module_path = Path("scripts/ingest_historical_kline.py").resolve()
    spec = importlib.util.spec_from_file_location("ingest_historical_kline_script", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    called = {"value": False}

    original_module = sys.modules.get("src.adapters.inbound.cli.historical_kline_cli")
    try:
        import src.adapters.inbound.cli.historical_kline_cli as cli_module

        monkeypatch.setattr(cli_module, "run_ingest_command", lambda: called.__setitem__("value", True))
        assert spec.loader is not None
        spec.loader.exec_module(module)
        module.main()
    finally:
        if original_module is not None:
            sys.modules["src.adapters.inbound.cli.historical_kline_cli"] = original_module

    assert called["value"] is True
