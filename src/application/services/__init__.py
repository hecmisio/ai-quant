"""Application services."""

from .a_share_ingestion import (
    AShareIngestionCommand,
    AShareIngestionSummary,
    AShareIngestionValidationError,
    QualityCheckResult,
    ingest_a_share_stock_list,
    make_batch_key,
    run_a_share_ingestion,
    validate_stock_list_for_ingestion,
)

__all__ = [
    "AShareIngestionCommand",
    "AShareIngestionSummary",
    "AShareIngestionValidationError",
    "QualityCheckResult",
    "ingest_a_share_stock_list",
    "make_batch_key",
    "run_a_share_ingestion",
    "validate_stock_list_for_ingestion",
]
