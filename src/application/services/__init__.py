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
from .macd import (
    MACDBacktestCommand,
    MACDSignalCommand,
    build_macd_strategy,
    export_macd_backtest_chart,
    run_macd_backtest_workflow,
    run_macd_signal_workflow,
)

__all__ = [
    "AShareIngestionCommand",
    "AShareIngestionSummary",
    "AShareIngestionValidationError",
    "MACDBacktestCommand",
    "MACDSignalCommand",
    "QualityCheckResult",
    "build_macd_strategy",
    "export_macd_backtest_chart",
    "ingest_a_share_stock_list",
    "make_batch_key",
    "run_macd_backtest_workflow",
    "run_macd_signal_workflow",
    "run_a_share_ingestion",
    "validate_stock_list_for_ingestion",
]
