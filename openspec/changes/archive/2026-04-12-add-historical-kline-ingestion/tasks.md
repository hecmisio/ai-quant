## 1. Ports And Domain Contracts

- [x] 1.1 Add application port definitions for historical K-line fetching and persistence governance.
- [x] 1.2 Add domain normalization helpers for provider-backed historical K-line data with stable market-bar fields.
- [x] 1.3 Add domain-level validation helpers for required columns, non-empty results, duplicate bar times, and OHLC price ordering.

## 2. Application Workflow

- [x] 2.1 Implement an application command, summary model, and error types for historical K-line ingestion.
- [x] 2.2 Implement the application workflow that resolves the instrument, fetches bars through the provider port, records quality checks, and finalizes the ingestion batch.
- [x] 2.3 Cover the application workflow with unit tests for success, validation failure, and missing-instrument failure paths.

## 3. Outbound Adapters

- [x] 3.1 Implement a market-data provider adapter that fetches historical K-line data from the chosen upstream source and maps raw fields into normalized bar columns.
- [x] 3.2 Extend ORM infrastructure as needed to represent `market_bars` in `db/models.py`.
- [x] 3.3 Implement a SQLAlchemy persistence gateway that resolves instruments, manages source and batch governance, and upserts `market_bars` rows by the Anne business key.

## 4. Inbound Workflow And Verification

- [x] 4.1 Add a CLI adapter and thin script entrypoint for running historical K-line ingestion manually.
- [x] 4.2 Add tests for the persistence gateway and CLI/script entrypoint behavior.
- [x] 4.3 Update contributor-facing documentation for the new historical K-line ingestion workflow and verify the full test suite passes.
