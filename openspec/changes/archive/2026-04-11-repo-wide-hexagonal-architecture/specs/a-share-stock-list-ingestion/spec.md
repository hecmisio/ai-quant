## MODIFIED Requirements

### Requirement: System MUST persist the normalized A-share stock list into Anne instruments
The system MUST provide an application-level workflow that takes the normalized A-share stock list and writes it into the Anne primary database `instruments` table through a persistence gateway, rather than coupling the use case directly to ORM or SQL details.

#### Scenario: Contributor runs the A-share stock list ingestion flow
- **WHEN** a contributor triggers the supported ingestion workflow for the normalized A-share stock list
- **THEN** the system MUST write corresponding records into the `instruments` table
- **AND** each stored record MUST preserve the stock's normalized symbol, name, and exchange identity

### Requirement: A-share stock list ingestion MUST record source and batch governance
The ingestion workflow MUST create or reuse source governance metadata and MUST create a batch record for each ingestion run so the loaded instruments can be traced to their origin, and those persistence responsibilities MUST be implemented behind a repository-defined gateway boundary.

#### Scenario: Team audits the origin of an ingested instrument batch
- **WHEN** a contributor reviews a completed A-share stock list ingestion run
- **THEN** the system MUST have a corresponding `data_sources` record for the source definition and an `ingestion_batches` record for that run
- **AND** the inserted or updated `instruments` rows MUST reference the relevant source and batch context

### Requirement: System MUST provide a script entrypoint for A-share stock list ingestion
The project MUST provide a supported script-level entrypoint so contributors can run the A-share stock list ingestion flow manually and inspect the outcome, and that entrypoint MUST act as an inbound adapter that wires together the provider, application service, and persistence adapter.

#### Scenario: Contributor runs the ingestion script manually
- **WHEN** a contributor runs the supported command-line entrypoint for A-share stock list ingestion
- **THEN** the project MUST execute the stock list fetch, validation, and database persistence flow
- **AND** the script MUST output an ingestion summary that is inspectable from the command line
