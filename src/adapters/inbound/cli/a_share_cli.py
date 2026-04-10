"""CLI adapters for A-share workflows."""

from __future__ import annotations

import argparse
from pathlib import Path

from scripts._common import ROOT, write_output_csv
from src.adapters.outbound.market_data import AkShareAStockListProvider
from src.adapters.outbound.persistence import SqlAlchemyAShareStockListGateway
from src.application.services import AShareIngestionSummary, AShareIngestionValidationError, ingest_a_share_stock_list
from db.session import create_anne_session


def build_fetch_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch the A-share stock list with AkShare.")
    parser.add_argument("--include-st", action="store_true", help="Include ST and *ST stocks in the output. B shares are still excluded.")
    parser.add_argument("--output-csv", help="Optional path for writing the filtered stock list to CSV.")
    return parser


def run_fetch_command() -> None:
    args = build_fetch_parser().parse_args()
    provider = AkShareAStockListProvider()
    stock_list = provider.fetch_stock_list(include_st=args.include_st)

    if args.output_csv:
        output_path = write_output_csv(stock_list, args.output_csv)
        print(f"Wrote stock list to {output_path}")
        return

    print(stock_list.to_string(index=False))


def build_ingest_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest the A-share stock list into Anne PostgreSQL.")
    parser.add_argument("--include-st", action="store_true", help="Include ST and *ST stocks during ingestion. B shares are still excluded.")
    parser.add_argument("--raw-uri", help="Optional raw source URI recorded on the ingestion batch and instruments.")
    parser.add_argument("--batch-key", help="Optional ingestion batch key. Defaults to a generated UTC timestamp key.")
    return parser


def print_ingestion_summary(summary: AShareIngestionSummary) -> None:
    print(f"Status: {summary.status}")
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
    provider = AkShareAStockListProvider()
    session = create_anne_session()
    gateway = SqlAlchemyAShareStockListGateway(session)
    raw_uri = args.raw_uri or str(Path(ROOT, "scripts", "ingest_a_share_stock_list.py"))
    try:
        summary = ingest_a_share_stock_list(
            gateway,
            provider=provider,
            include_st=args.include_st,
            batch_key=args.batch_key,
            raw_uri=raw_uri,
        )
    except AShareIngestionValidationError as exc:
        print_ingestion_summary(exc.summary)
        raise SystemExit(1) from exc
    finally:
        session.close()

    print_ingestion_summary(summary)
