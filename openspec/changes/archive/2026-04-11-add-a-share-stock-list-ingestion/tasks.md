## 1. Ingestion Core

- [x] 1.1 Add an A-share stock list ingestion module that reuses the normalized AkShare stock list fetch flow.
- [x] 1.2 Implement source registration and per-run ingestion batch creation for the A-share stock list load.
- [x] 1.3 Implement idempotent `instruments` upsert logic keyed by `(exchange, symbol)` with controlled field mapping.
- [x] 1.4 Add batch-level quality checks for empty required fields, duplicate business keys, and non-empty stock list results.

## 2. Script Entry Point

- [x] 2.1 Add a command-line script that runs the A-share stock list ingestion workflow against the Anne database.
- [x] 2.2 Make the script print an ingestion summary including inserted or updated counts, batch identity, and quality check outcomes.

## 3. Verification

- [x] 3.1 Add or update tests for field mapping, idempotent upsert behavior, and governance record creation.
- [x] 3.2 Run the relevant automated tests for the A-share ingestion flow.
- [x] 3.3 Execute a local end-to-end ingestion check against the Anne PostgreSQL environment and confirm expected records are created.
