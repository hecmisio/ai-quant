## ADDED Requirements

### Requirement: System MUST persist the normalized A-share stock list into Anne instruments
The system MUST provide a workflow that takes the normalized A-share stock list and writes it into the Anne primary database `instruments` table.

#### Scenario: Contributor runs the A-share stock list ingestion flow
- **WHEN** a contributor triggers the supported ingestion workflow for the normalized A-share stock list
- **THEN** the system MUST write corresponding records into the `instruments` table
- **AND** each stored record MUST preserve the stock's normalized symbol, name, and exchange identity

### Requirement: A-share stock list ingestion MUST be idempotent on instrument business identity
The ingestion workflow MUST use the `instruments` business identity so that repeated runs do not create duplicate records for the same A-share stock.

#### Scenario: Same stock list is ingested more than once
- **WHEN** the ingestion workflow processes rows that map to an existing `instruments(exchange, symbol)` identity
- **THEN** the system MUST update or retain the existing instrument record instead of inserting a duplicate
- **AND** the database MUST continue to satisfy the unique identity for that instrument

### Requirement: A-share stock list ingestion MUST record source and batch governance
The ingestion workflow MUST create or reuse source governance metadata and MUST create a batch record for each ingestion run so the loaded instruments can be traced to their origin.

#### Scenario: Team audits the origin of an ingested instrument batch
- **WHEN** a contributor reviews a completed A-share stock list ingestion run
- **THEN** the system MUST have a corresponding `data_sources` record for the source definition and an `ingestion_batches` record for that run
- **AND** the inserted or updated `instruments` rows MUST reference the relevant source and batch context

### Requirement: A-share stock list ingestion MUST record batch-level quality checks
The ingestion workflow MUST execute and persist basic batch-level quality checks before or during database write so structural data issues are visible in governance records.

#### Scenario: Batch completes with structural validation results
- **WHEN** the ingestion workflow completes validation for a stock list batch
- **THEN** the system MUST store one or more `quality_checks` records for that batch
- **AND** the checks MUST cover at least non-empty required fields or duplicate business-key validation

### Requirement: System MUST provide a script entrypoint for A-share stock list ingestion
The project MUST provide a supported script-level entrypoint so contributors can run the A-share stock list ingestion flow manually and inspect the outcome.

#### Scenario: Contributor runs the ingestion script manually
- **WHEN** a contributor runs the supported command-line entrypoint for A-share stock list ingestion
- **THEN** the project MUST execute the stock list fetch, validation, and database persistence flow
- **AND** the script MUST output an ingestion summary that is inspectable from the command line
