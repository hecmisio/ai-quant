# anne-database-bootstrap Specification

## Purpose
TBD - created by archiving change add-postgres-18-bootstrap. Update Purpose after archive.
## Requirements
### Requirement: Repository MUST provide a PostgreSQL 18.3 bootstrap service
The repository MUST provide a Docker Compose based database bootstrap entrypoint for Anne's primary database, and that service MUST use PostgreSQL 18.3 as the pinned base version.

#### Scenario: Developer starts the Anne database locally
- **WHEN** a developer starts the repository database service through the documented Compose entrypoint
- **THEN** the repository MUST start a PostgreSQL service pinned to version 18.3
- **AND** the service MUST expose configurable connection settings for database name, username, password, and host port

### Requirement: Database bootstrap MUST initialize required extensions
The Anne primary database bootstrap MUST initialize the required extensions for time-series and vector retrieval capabilities so that downstream schema work can rely on them being available from the first successful database creation.

#### Scenario: First-time database initialization
- **WHEN** the PostgreSQL data directory is created for the first time
- **THEN** the bootstrap process MUST execute repository-managed initialization SQL
- **AND** that initialization SQL MUST enable the `timescaledb` and `vector` extensions in the target database

### Requirement: Database bootstrap MUST persist state and initialization assets predictably
The repository MUST define a stable persistence and initialization layout for the Anne database so that local development can restart safely and contributors can locate the initialization assets in version control.

#### Scenario: Developer restarts the local database service
- **WHEN** the database container is stopped and started again after initial setup
- **THEN** the PostgreSQL data directory MUST persist across restarts
- **AND** the repository MUST keep initialization scripts in a dedicated mounted directory that is separate from the persistent data volume

### Requirement: Bootstrap scope MUST remain limited to infrastructure baseline
The initial Anne database bootstrap MUST establish only the infrastructure baseline and MUST NOT predefine business tables or domain schemas that belong to later data-modeling changes.

#### Scenario: Team uses the bootstrap as the starting point for later schema work
- **WHEN** contributors inspect or apply the initial database bootstrap change
- **THEN** they MUST find only infrastructure-level setup such as service configuration and extension initialization
- **AND** they MUST NOT find pre-created Anne business tables presented as part of the bootstrap baseline

