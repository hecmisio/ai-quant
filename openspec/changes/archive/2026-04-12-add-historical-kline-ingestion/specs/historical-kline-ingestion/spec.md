## ADDED Requirements

### Requirement: System MUST provide a reusable historical K-line fetcher behind a provider port
The system MUST provide a reusable outbound provider contract for fetching historical K-line data for a target instrument, and the concrete implementation MUST hide raw SDK calls and provider-specific field names from the application layer.

#### Scenario: Application workflow requests historical bars for an instrument
- **WHEN** the historical K-line ingestion workflow requests bars for a target instrument, timeframe, and adjustment mode
- **THEN** the system MUST fetch those bars through a provider adapter exposed through an application-defined port
- **AND** the returned dataset MUST be normalized into stable project-facing fields instead of raw provider column names

### Requirement: Historical K-line ingestion MUST persist normalized bars into Anne market_bars
The system MUST provide an application-level ingestion workflow that accepts normalized historical K-line data for a resolved instrument and persists those bars into Anne `market_bars` through a persistence gateway rather than coupling the use case directly to ORM or SQL details.

#### Scenario: Contributor runs a supported historical K-line ingestion flow
- **WHEN** a contributor triggers the supported ingestion workflow for a known instrument
- **THEN** the system MUST write corresponding rows into `market_bars`
- **AND** each stored row MUST preserve the instrument identity, bar time, timeframe, adjustment type, and normalized OHLCV fields

### Requirement: Historical K-line ingestion MUST record source, batch, and quality governance
The ingestion workflow MUST create or reuse source governance metadata, MUST create a batch record for each run, and MUST record quality-check outcomes so every persisted historical-bar load can be traced and audited.

#### Scenario: Team audits a completed historical K-line ingestion run
- **WHEN** a contributor reviews a completed historical K-line ingestion batch
- **THEN** the system MUST have corresponding `data_sources`, `ingestion_batches`, and `quality_checks` records for that run
- **AND** the inserted or updated `market_bars` rows MUST reference the relevant source and batch context

### Requirement: Historical K-line ingestion MUST fail clearly when the target instrument cannot be resolved
The historical K-line ingestion workflow MUST require a resolvable target instrument from Anne `instruments` before writing bars, and it MUST fail with a clear error instead of creating orphaned market data.

#### Scenario: Contributor requests bars for an unknown instrument
- **WHEN** the workflow receives an exchange and symbol that do not resolve to an existing Anne instrument
- **THEN** the workflow MUST stop before writing any `market_bars` rows
- **AND** the failure MUST clearly indicate that the instrument must already exist in `instruments`

### Requirement: System MUST provide a script entrypoint for historical K-line ingestion
The project MUST provide a supported script-level entrypoint for historical K-line ingestion, and that entrypoint MUST act as a thin inbound adapter that wires together provider, application service, and persistence gateway components.

#### Scenario: Contributor runs the historical K-line ingestion entrypoint manually
- **WHEN** a contributor runs the supported command-line entrypoint for historical K-line ingestion
- **THEN** the project MUST execute the fetch, normalization, validation, and database persistence flow through the repository's defined boundaries
- **AND** the command MUST output an ingestion summary that is inspectable from the command line
