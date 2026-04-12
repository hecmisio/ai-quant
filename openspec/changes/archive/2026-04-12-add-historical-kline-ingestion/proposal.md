## Why

The repository already supports stock-universe ingestion and has an Anne schema for `market_bars`, but it still lacks a supported workflow for fetching an instrument's historical K-line data and persisting those bars into the primary database. This gap blocks downstream research, charting, and future factor or backtest workflows from relying on a governed historical market-data source.

## What Changes

- Add a supported workflow that fetches historical K-line data for a target instrument through a provider adapter and persists normalized bars into Anne `market_bars`.
- Add application-level validation and ingestion governance for historical K-line batches, including source metadata, batch records, and quality-check recording.
- Add persistence support for resolving the target instrument and upserting or versioning K-line bars by instrument, bar time, timeframe, and adjustment type.
- Add a script or CLI entrypoint so contributors can run historical K-line ingestion manually and inspect the ingestion summary.
- Keep external SDK details, raw field mapping, and persistence logic behind hexagonal boundaries rather than embedding them in scripts.

## Capabilities

### New Capabilities
- `historical-kline-ingestion`: Fetch, normalize, validate, and persist instrument historical K-line data into Anne `market_bars` with source and batch governance.

### Modified Capabilities
- None.

## Impact

- Affected code: `src/application/ports/`, `src/application/services/`, `src/domain/market_data/`, `src/adapters/outbound/market_data/`, `src/adapters/outbound/persistence/`, `src/adapters/inbound/cli/`, `scripts/`, `db/`, `tests/`.
- Affected systems: AkShare-backed market-data access, Anne PostgreSQL persistence, ingestion governance tables, and CLI/manual ingestion workflows.
- Dependencies: existing `instruments`, `data_sources`, `ingestion_batches`, `quality_checks`, and `market_bars` schema contracts.
