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
from .historical_kline_ingestion import (
    HistoricalKlineIngestionCommand,
    HistoricalKlineIngestionSummary,
    HistoricalKlineIngestionValidationError,
    HistoricalKlineInstrumentNotFoundError,
    ingest_historical_kline,
    make_historical_kline_batch_key,
    run_historical_kline_ingestion,
)

__all__ = [
    "AShareIngestionCommand",
    "AShareIngestionSummary",
    "AShareIngestionValidationError",
    "HistoricalKlineIngestionCommand",
    "HistoricalKlineIngestionSummary",
    "HistoricalKlineIngestionValidationError",
    "HistoricalKlineInstrumentNotFoundError",
    "QualityCheckResult",
    "ingest_historical_kline",
    "ingest_a_share_stock_list",
    "make_batch_key",
    "make_historical_kline_batch_key",
    "run_a_share_ingestion",
    "run_historical_kline_ingestion",
    "validate_stock_list_for_ingestion",
]
