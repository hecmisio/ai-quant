"""Application service for A-share stock list ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from src.application.ports import AShareStockListGateway, AShareStockListProvider


DEFAULT_SOURCE_CODE = "akshare_a_share_stock_list"
DEFAULT_SOURCE_NAME = "AkShare A-share Stock List"
DEFAULT_SOURCE_TYPE = "market"
DEFAULT_INSTRUMENT_TYPE = "equity"
DEFAULT_CURRENCY = "CNY"
DEFAULT_STATUS = "active"


@dataclass(frozen=True)
class QualityCheckResult:
    check_name: str
    check_status: str
    severity: str
    details: dict[str, Any]

    @property
    def passed(self) -> bool:
        return self.check_status == "passed"


@dataclass(frozen=True)
class AShareIngestionCommand:
    include_st: bool = False
    batch_key: str | None = None
    source_code: str = DEFAULT_SOURCE_CODE
    source_name: str = DEFAULT_SOURCE_NAME
    source_type: str = DEFAULT_SOURCE_TYPE
    raw_uri: str | None = None
    as_of: datetime | None = None


@dataclass(frozen=True)
class AShareIngestionSummary:
    source_id: int
    batch_id: int
    batch_key: str
    fetched_rows: int
    inserted_rows: int
    updated_rows: int
    quality_checks: tuple[QualityCheckResult, ...]
    status: str

    @property
    def failed_checks(self) -> tuple[QualityCheckResult, ...]:
        return tuple(check for check in self.quality_checks if not check.passed)


class AShareIngestionValidationError(RuntimeError):
    def __init__(self, summary: AShareIngestionSummary):
        self.summary = summary
        super().__init__(f"A-share stock list ingestion failed validation for batch {summary.batch_key}")


def make_batch_key(now: datetime | None = None) -> str:
    timestamp = (now or datetime.now(UTC)).astimezone(UTC)
    return f"a_share_stock_list_{timestamp.strftime('%Y%m%dT%H%M%SZ')}"


def validate_stock_list_for_ingestion(stock_list: pd.DataFrame) -> list[QualityCheckResult]:
    required_columns = ("symbol", "name", "exchange")
    missing_columns = [column for column in required_columns if column not in stock_list.columns]
    if missing_columns:
        raise ValueError(f"stock list missing required columns: {missing_columns}")

    empty_required_rows = int(
        stock_list.loc[:, list(required_columns)]
        .fillna("")
        .astype(str)
        .apply(lambda value: value.str.strip())
        .eq("")
        .any(axis=1)
        .sum()
    )
    duplicate_key_count = int(stock_list.duplicated(subset=["exchange", "symbol"]).sum())
    total_rows = int(len(stock_list))

    return [
        QualityCheckResult("stock_list_not_empty", "passed" if total_rows > 0 else "failed", "info" if total_rows > 0 else "error", {"row_count": total_rows}),
        QualityCheckResult(
            "required_fields_not_empty",
            "passed" if empty_required_rows == 0 else "failed",
            "info" if empty_required_rows == 0 else "error",
            {"empty_required_rows": empty_required_rows, "required_fields": list(required_columns)},
        ),
        QualityCheckResult(
            "instrument_business_keys_unique",
            "passed" if duplicate_key_count == 0 else "failed",
            "info" if duplicate_key_count == 0 else "error",
            {"duplicate_business_keys": duplicate_key_count},
        ),
    ]


def ingest_a_share_stock_list(
    gateway: AShareStockListGateway,
    *,
    include_st: bool = False,
    provider: AShareStockListProvider,
    batch_key: str | None = None,
    source_code: str = DEFAULT_SOURCE_CODE,
    source_name: str = DEFAULT_SOURCE_NAME,
    source_type: str = DEFAULT_SOURCE_TYPE,
    raw_uri: str | None = None,
    as_of: datetime | None = None,
) -> AShareIngestionSummary:
    command = AShareIngestionCommand(
        include_st=include_st,
        batch_key=batch_key,
        source_code=source_code,
        source_name=source_name,
        source_type=source_type,
        raw_uri=raw_uri,
        as_of=as_of,
    )
    return run_a_share_ingestion(gateway, provider=provider, command=command)


def run_a_share_ingestion(
    gateway: AShareStockListGateway,
    *,
    provider: AShareStockListProvider,
    command: AShareIngestionCommand,
) -> AShareIngestionSummary:
    stock_list = provider.fetch_stock_list(include_st=command.include_st)
    quality_checks = tuple(validate_stock_list_for_ingestion(stock_list))
    batch_time = command.as_of or datetime.now(UTC)
    resolved_batch_key = command.batch_key or make_batch_key(batch_time)

    source_id = gateway.ensure_source(
        source_code=command.source_code,
        source_name=command.source_name,
        source_type=command.source_type,
        description="Normalized A-share stock list sourced from AkShare.",
        metadata={"provider": "akshare", "dataset": "a_share_stock_list", "include_st": command.include_st},
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
            notes="A-share stock list validation failed",
            now=batch_time,
        )
        summary = AShareIngestionSummary(
            source_id=source_id,
            batch_id=batch_id,
            batch_key=resolved_batch_key,
            fetched_rows=int(len(stock_list)),
            inserted_rows=0,
            updated_rows=0,
            quality_checks=quality_checks,
            status="failed",
        )
        raise AShareIngestionValidationError(summary)

    inserted_rows, updated_rows = gateway.upsert_instruments(
        stock_list=stock_list,
        source_id=source_id,
        batch_id=batch_id,
        instrument_type=DEFAULT_INSTRUMENT_TYPE,
        currency=DEFAULT_CURRENCY,
        status=DEFAULT_STATUS,
        raw_uri=command.raw_uri,
        as_of=batch_time,
    )
    gateway.finalize_batch(
        batch_id=batch_id,
        status="completed",
        row_count=int(len(stock_list)),
        error_count=0,
        notes=f"Inserted {inserted_rows} and updated {updated_rows} A-share instruments",
        now=batch_time,
    )
    return AShareIngestionSummary(
        source_id=source_id,
        batch_id=batch_id,
        batch_key=resolved_batch_key,
        fetched_rows=int(len(stock_list)),
        inserted_rows=inserted_rows,
        updated_rows=updated_rows,
        quality_checks=quality_checks,
        status="completed",
    )


def to_gateway_quality_check_payload(check: QualityCheckResult) -> dict[str, Any]:
    return {
        "check_name": check.check_name,
        "check_status": check.check_status,
        "severity": check.severity,
        "details": check.details,
    }
