"""CLI adapters for historical K-line ingestion workflows."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import os
from pathlib import Path
import threading

from sqlalchemy.engine import Engine

from db.session import create_anne_engine, create_anne_session
from scripts._common import ROOT
from src.adapters.outbound.market_data import AkShareHistoricalKlineProvider
from src.adapters.outbound.persistence import SqlAlchemyHistoricalKlineGateway
from src.application.services import (
    HistoricalKlineIngestionSummary,
    HistoricalKlineIngestionValidationError,
    HistoricalKlineInstrumentNotFoundError,
    ingest_historical_kline,
)


@dataclass(frozen=True)
class BulkHistoricalKlineResult:
    exchange: str
    symbol: str
    success: bool
    summary: HistoricalKlineIngestionSummary | None = None
    error: str | None = None


def build_ingest_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch and ingest historical K-line data into Anne PostgreSQL.")
    parser.add_argument("--exchange", help="Instrument exchange code, e.g. SSE or SZSE.")
    parser.add_argument("--symbol", help="Instrument symbol code, e.g. 600519.")
    parser.add_argument("--all-instruments", action="store_true", help="Fetch and ingest historical K-line data for all matching Anne instruments.")
    parser.add_argument("--instrument-type", default="equity", help="Instrument type filter for --all-instruments mode. Default: equity.")
    parser.add_argument("--instrument-status", default="active", help="Instrument status filter for --all-instruments mode. Default: active.")
    parser.add_argument("--max-workers", type=int, default=min(8, (os.cpu_count() or 4) * 2), help="Maximum concurrent workers for --all-instruments mode.")
    parser.add_argument("--timeframe", default="1d", help="Bar timeframe. Supported in v1: 1d, 1w, 1m.")
    parser.add_argument("--adjustment-type", default="none", help="Adjustment type. Supported in v1: none, qfq, hfq.")
    parser.add_argument("--start-date", help="Optional inclusive start date in YYYY-MM-DD format.")
    parser.add_argument("--end-date", help="Optional inclusive end date in YYYY-MM-DD format.")
    parser.add_argument("--raw-uri", help="Optional raw source URI recorded on the ingestion batch and bars.")
    parser.add_argument("--batch-key", help="Optional ingestion batch key. Defaults to a generated UTC timestamp key.")
    return parser


def print_ingestion_summary(summary: HistoricalKlineIngestionSummary) -> None:
    print(f"Status: {summary.status}")
    print(f"Exchange: {summary.exchange}")
    print(f"Symbol: {summary.symbol}")
    print(f"Timeframe: {summary.timeframe}")
    print(f"Adjustment Type: {summary.adjustment_type}")
    print(f"Instrument ID: {summary.instrument_id}")
    print(f"Batch ID: {summary.batch_id}")
    print(f"Batch Key: {summary.batch_key}")
    print(f"Source ID: {summary.source_id}")
    print(f"Fetched Rows: {summary.fetched_rows}")
    print(f"Inserted Rows: {summary.inserted_rows}")
    print(f"Updated Rows: {summary.updated_rows}")
    print("Quality Checks:")
    for check in summary.quality_checks:
        print(
            f"  - {check.check_name}: {check.check_status} "
            f"(severity={check.severity}, details={check.details})"
        )


def run_ingest_command() -> None:
    args = build_ingest_parser().parse_args()
    raw_uri = args.raw_uri or str(Path(ROOT, "scripts", "ingest_historical_kline.py"))
    if args.all_instruments:
        if args.exchange or args.symbol:
            raise SystemExit("--all-instruments cannot be combined with --exchange or --symbol")
        run_bulk_ingest_command(args=args, raw_uri=raw_uri)
        return

    if not args.exchange or not args.symbol:
        raise SystemExit("single-instrument mode requires both --exchange and --symbol")

    provider = AkShareHistoricalKlineProvider()
    session = create_anne_session()
    gateway = SqlAlchemyHistoricalKlineGateway(session)
    try:
        summary = ingest_historical_kline(
            gateway,
            provider=provider,
            exchange=args.exchange,
            symbol=args.symbol,
            timeframe=args.timeframe,
            adjustment_type=args.adjustment_type,
            start_date=args.start_date,
            end_date=args.end_date,
            batch_key=args.batch_key,
            raw_uri=raw_uri,
        )
    except HistoricalKlineInstrumentNotFoundError as exc:
        raise SystemExit(str(exc)) from exc
    except HistoricalKlineIngestionValidationError as exc:
        print_ingestion_summary(exc.summary)
        raise SystemExit(1) from exc
    finally:
        session.close()

    print_ingestion_summary(summary)


def run_bulk_ingest_command(*, args: argparse.Namespace, raw_uri: str) -> None:
    engine = create_anne_engine()
    session = create_anne_session(engine=engine)
    gateway = SqlAlchemyHistoricalKlineGateway(session)
    try:
        instruments = gateway.list_instruments(
            instrument_type=args.instrument_type,
            status=args.instrument_status,
        )
    finally:
        session.close()

    if not instruments:
        raise SystemExit("No Anne instruments matched the requested filters.")

    total = len(instruments)
    completed = 0
    successes = 0
    failures = 0
    total_inserted = 0
    total_updated = 0
    results: list[BulkHistoricalKlineResult] = []
    progress_lock = threading.Lock()
    _print_progress(completed=0, total=total, successes=0, failures=0)

    with ThreadPoolExecutor(max_workers=max(1, args.max_workers)) as executor:
        futures = [
            executor.submit(
                _ingest_one_instrument,
                engine=engine,
                exchange=str(item["exchange"]),
                symbol=str(item["symbol"]),
                timeframe=args.timeframe,
                adjustment_type=args.adjustment_type,
                start_date=args.start_date,
                end_date=args.end_date,
                raw_uri=raw_uri,
            )
            for item in instruments
        ]

        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            with progress_lock:
                completed += 1
                if result.success and result.summary is not None:
                    successes += 1
                    total_inserted += result.summary.inserted_rows
                    total_updated += result.summary.updated_rows
                else:
                    failures += 1
                _print_progress(
                    completed=completed,
                    total=total,
                    successes=successes,
                    failures=failures,
                )

    print()
    print("Bulk Historical K-line Ingestion Summary:")
    print(f"Total Instruments: {total}")
    print(f"Succeeded: {successes}")
    print(f"Failed: {failures}")
    print(f"Inserted Rows: {total_inserted}")
    print(f"Updated Rows: {total_updated}")
    failed_results = [item for item in results if not item.success]
    if failed_results:
        print("Failures:")
        for item in failed_results[:20]:
            print(f"  - {item.exchange}:{item.symbol} -> {item.error}")
        if len(failed_results) > 20:
            print(f"  - ... and {len(failed_results) - 20} more")


def _ingest_one_instrument(
    *,
    engine: Engine,
    exchange: str,
    symbol: str,
    timeframe: str,
    adjustment_type: str,
    start_date: str | None,
    end_date: str | None,
    raw_uri: str,
) -> BulkHistoricalKlineResult:
    session = create_anne_session(engine=engine)
    gateway = SqlAlchemyHistoricalKlineGateway(session)
    provider = AkShareHistoricalKlineProvider()
    try:
        summary = ingest_historical_kline(
            gateway,
            provider=provider,
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe,
            adjustment_type=adjustment_type,
            start_date=start_date,
            end_date=end_date,
            raw_uri=raw_uri,
        )
        return BulkHistoricalKlineResult(exchange=exchange, symbol=symbol, success=True, summary=summary)
    except (HistoricalKlineInstrumentNotFoundError, HistoricalKlineIngestionValidationError, RuntimeError, ValueError) as exc:
        return BulkHistoricalKlineResult(exchange=exchange, symbol=symbol, success=False, error=str(exc))
    finally:
        session.close()


def _print_progress(*, completed: int, total: int, successes: int, failures: int) -> None:
    width = 30
    ratio = (completed / total) if total else 1.0
    filled = int(width * ratio)
    bar = "#" * filled + "-" * (width - filled)
    print(
        f"\rProgress [{bar}] {completed}/{total} | success={successes} failure={failures}",
        end="",
        flush=True,
    )
