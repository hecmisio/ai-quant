# anne-core-tables Specification

## Purpose
TBD - created by archiving change add-anne-core-tables. Update Purpose after archive.
## Requirements
### Requirement: Anne primary database MUST provide governance tables for source tracking
The Anne primary database MUST provide a first version of governance tables that track data sources, ingestion batches, and quality check outcomes so that downstream facts can be traced back to their origin and loading process.

#### Scenario: Team inspects provenance for ingested records
- **WHEN** a contributor loads standardized data into the Anne database
- **THEN** the schema MUST provide tables for data sources, ingestion batches, and quality checks
- **AND** those tables MUST allow downstream fact records to reference their source and ingestion context

### Requirement: Anne primary database MUST provide core fact tables for the initial data domains
The Anne primary database MUST provide a first version of core fact or metadata tables for the initial Anne data domains, including instruments, market bars, financial reports, macroeconomic series, documents, calendar events, and catalyst events.

#### Scenario: Team prepares the first multi-domain data loads
- **WHEN** contributors prepare to ingest market, financial, macro, document, calendar, and catalyst data into Anne
- **THEN** the schema MUST provide dedicated relational tables for those initial data domains
- **AND** the schema MUST NOT rely on a single catch-all JSON table as the primary storage model for all domains

### Requirement: Core Anne tables MUST use consistent governance columns
Each core Anne governance table and fact table MUST follow a consistent governance-column baseline that supports lineage, versioning, and raw-file traceability.

#### Scenario: Contributor compares two fact tables for auditability
- **WHEN** a contributor inspects different Anne core tables
- **THEN** those tables MUST use a consistent baseline for governance fields such as source identity, ingestion time, effective time, version, and raw location
- **AND** the schema MUST preserve those columns even when specific business fields differ by domain

### Requirement: Core Anne tables MUST enforce business uniqueness and relational integrity
The Anne primary database schema MUST define explicit keys, unique constraints, and foreign-key relationships for core tables so that duplicate standardized facts are constrained and cross-table references remain valid.

#### Scenario: Duplicate or invalid records are inserted
- **WHEN** a loader attempts to insert duplicate business facts or references a missing parent record
- **THEN** the schema MUST enforce uniqueness for the relevant business identity of the record
- **AND** the schema MUST reject invalid foreign-key references where parent-child relationships are required

### Requirement: First-version schema MUST remain extensible for later TimescaleDB and vector enhancements
The first-version Anne table schema MUST be designed so that later changes can add hypertables, vector columns, or richer relation tables without replacing the initial relational baseline.

#### Scenario: Team expands time-series or semantic retrieval capabilities later
- **WHEN** a later change adds TimescaleDB hypertables or pgvector-backed retrieval structures
- **THEN** the initial Anne schema MUST already separate core facts clearly enough to support those upgrades
- **AND** the first-version schema MUST NOT depend on those later optimizations to function correctly

