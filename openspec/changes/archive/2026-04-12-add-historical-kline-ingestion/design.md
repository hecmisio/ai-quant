## Context

The repository already has three pieces needed for historical K-line ingestion, but they are not yet connected into a supported workflow:

- Anne schema support already exists for governed market-bar persistence through `data_sources`, `ingestion_batches`, `quality_checks`, `instruments`, and `market_bars`.
- The codebase already uses a hexagonal ingestion pattern for A-share stock-list ingestion, with application ports, outbound adapters, and CLI wiring.
- K-line normalization logic already exists for CSV-based inputs, but there is no provider-backed workflow that fetches historical bars for a known instrument and writes them into `market_bars`.

This change needs to fit the existing repository direction:

- external market-data access must stay behind an outbound provider port
- database writes must stay behind an outbound gateway port
- application services must own orchestration, validation, and ingestion governance
- scripts and CLI adapters must stay thin

The immediate stakeholder is the data-ingestion path for Anne. The downstream beneficiaries are charting, future factor pipelines, and any research workflow that needs governed historical OHLCV data.

## Goals / Non-Goals

**Goals:**

- Define a supported workflow for fetching historical K-line data for a target instrument and persisting normalized bars into Anne `market_bars`.
- Reuse the existing governance pattern so every ingestion run records source metadata, batch metadata, and quality checks.
- Keep instrument resolution explicit so bars are always linked to an existing `instruments` row rather than creating orphaned market data.
- Normalize provider-specific field names into a stable project-facing structure before persistence.
- Support manual execution through a CLI/script entrypoint with an inspectable ingestion summary.

**Non-Goals:**

- Adding a full query API for reading historical bars back out of Anne.
- Supporting every market-data source in the first version; one provider-backed implementation is enough.
- Introducing realtime streaming, websocket feeds, or incremental intraday refresh scheduling.
- Redesigning the Anne schema for `market_bars`; the current schema is assumed to be the target storage contract.
- Solving future factor, backtest, or portfolio workflows in the same change.

## Decisions

### 1. Model the workflow after the existing governed stock-list ingestion pattern

The implementation should follow the same architectural shape already used by `a_share_ingestion`:

- application command + summary objects
- provider port for external fetch
- gateway port for persistence and governance
- CLI adapter that wires provider, gateway, and session factory together

Reasoning:

- This keeps ingestion workflows consistent across the repository.
- It reduces ambiguity around where validation, batching, and summary reporting belong.
- It allows tests to mirror the existing unit-testing style used for stock-list ingestion.

Alternatives considered:

- Write a direct script that fetches data and inserts rows with SQLAlchemy inline. Rejected because it breaks the hexagonal boundary and duplicates governance logic.
- Put orchestration into the persistence adapter. Rejected because source fetching, validation, and batch control are application concerns, not storage concerns.

### 2. Require prior instrument existence instead of auto-creating instruments during K-line ingestion

The historical K-line ingestion workflow should resolve the target instrument through the existing `instruments` table and fail clearly if the requested `(exchange, symbol)` is missing.

Reasoning:

- `market_bars` is a fact table and should point to a governed instrument identity.
- The repository already has a separate stock-universe ingestion flow that owns instrument creation.
- Failing early avoids mixing two distinct data-governance responsibilities into one workflow.

Alternatives considered:

- Auto-create missing instruments during bar ingestion. Rejected because it weakens instrument governance and creates partial or inconsistent identities.
- Store bars keyed only by symbol/exchange without `instrument_id`. Rejected because it conflicts with the current Anne schema.

### 3. Normalize fetched bars into a stable project-facing dataframe before persistence

The provider adapter may deal with AkShare-specific parameters and raw columns, but the application layer should operate on a stable normalized structure such as:

- `bar_time`
- `open_price`
- `high_price`
- `low_price`
- `close_price`
- `volume`
- optional `turnover`
- optional `trade_count`

The normalized dataset should also carry stable ingestion dimensions:

- `timeframe`
- `adjustment_type`

Reasoning:

- It prevents provider field names from leaking into application logic.
- It creates a reusable normalization boundary for later providers.
- It aligns the in-memory representation with the target `market_bars` table.

Alternatives considered:

- Persist raw provider output directly and map columns inside SQLAlchemy code. Rejected because it couples storage logic to upstream SDK semantics.

### 4. Use governed batch-level validation before writing bars

The application service should validate at least:

- required OHLCV/time columns exist after normalization
- the result is not empty
- `bar_time` values are unique within the batch for the selected `(instrument, timeframe, adjustment_type)`
- numeric OHLC values are parseable
- each row preserves a valid price ordering expectation such as `low <= open/high/close <= high`

Validation outcomes should be written to `quality_checks` before any final batch completion.

Reasoning:

- Historical bars become foundational data for later analytics, so silent corruption is costly.
- The repository already treats governance metadata as first-class ingestion output.

Alternatives considered:

- Only rely on database uniqueness errors. Rejected because that catches too little and produces poor operator feedback.
- Validate inside the CLI. Rejected because validation belongs in the application workflow and should be testable without a shell.

### 5. Upsert bars using the existing market-bar business key dimensions

Persistence should treat `(instrument_id, bar_time, timeframe, adjustment_type, version)` as the governing business key and default to `version = 1`. The first implementation should update existing rows for the same version rather than inserting duplicates.

Reasoning:

- It matches the current Anne uniqueness contract.
- It gives the workflow deterministic rerun behavior for a repeated historical load.
- It avoids making version management mandatory before the first ingestion path exists.

Alternatives considered:

- Always insert a new version on rerun. Rejected for v1 because it complicates idempotence and operator expectations.
- Delete and replace the entire bar range before writing. Rejected because it is more destructive than necessary.

## Risks / Trade-offs

- [Provider output may vary across symbols, timeframes, or adjustment modes] -> Mitigation: normalize all provider-specific fields in the outbound adapter and validate the normalized dataframe before persistence.
- [Historical reruns could overwrite previously cleaned data for the same business key] -> Mitigation: keep version explicit in the workflow contract and default to deterministic `version = 1` behavior for v1.
- [Instrument lookup failures could frustrate manual users] -> Mitigation: make the CLI summary and error message explicitly state that the instrument must exist in `instruments` first.
- [Large historical windows may create heavy batch writes] -> Mitigation: keep the first version scoped to correctness and stable upsert behavior; optimize batch insert/update strategy after a working path exists.

## Migration Plan

1. Add a new capability spec for historical K-line ingestion.
2. Add provider and gateway ports plus an application workflow for normalized historical-bar ingestion.
3. Implement a provider adapter, persistence adapter, and CLI/script entrypoint.
4. Add tests for normalization, validation, persistence orchestration, and CLI execution.
5. Use the supported CLI flow after instrument ingestion has already populated `instruments`.

Rollback strategy:

- If the workflow design proves incorrect, the code can be reverted without schema rollback because the required Anne tables already exist.
- If a bad ingestion run reaches the database, rollback happens operationally by deleting or correcting affected `market_bars` rows and related batch records for that source and batch key.

## Open Questions

- Which provider and parameter surface should be the first supported implementation for historical bars: daily A-share bars only, or should the contract already name intraday timeframes?
- Should the first CLI require both `exchange` and `symbol`, or should it also support resolving by a single normalized instrument identifier in the future?
- Do we want the first version to persist optional provider fields such as turnover and trade count when present, or should those remain nullable unless consistently available?
