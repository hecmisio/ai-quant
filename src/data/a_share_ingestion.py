"""Compatibility facade for the A-share ingestion application service."""

from src.application.ports.a_share import AShareStockListGateway
from src.application.services.a_share_ingestion import (
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
    "AShareStockListGateway",
    "QualityCheckResult",
    "ingest_a_share_stock_list",
    "make_batch_key",
    "run_a_share_ingestion",
    "validate_stock_list_for_ingestion",
]
