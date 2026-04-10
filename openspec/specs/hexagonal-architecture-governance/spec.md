## ADDED Requirements

### Requirement: Repository MUST define explicit hexagonal architecture layers for new core code
The repository MUST define explicit hexagonal architecture layer responsibilities for `domain`, `application`, `adapters`, and `db` so that new core capabilities are implemented with clear dependency direction and boundary ownership.

#### Scenario: Contributor adds a new cross-module capability
- **WHEN** a contributor adds a new core capability that touches business rules, external integrations, or execution flow
- **THEN** the repository MUST provide explicit layer roles for domain rules, use-case orchestration, inbound or outbound adapters, and database infrastructure
- **AND** the new capability MUST NOT place all of those concerns into a single unlayered module

### Requirement: External integrations MUST enter the system through explicit ports and adapters
The repository MUST define explicit provider, gateway, repository, or equivalent ports for external dependencies, and MUST implement those ports through adapters instead of letting application logic depend directly on SDKs, filesystems, or ORM infrastructure.

#### Scenario: Contributor integrates an external dependency
- **WHEN** a contributor introduces or extends an integration for AkShare, filesystem I/O, database persistence, or other external systems
- **THEN** the application layer MUST depend on an explicit port contract for that integration
- **AND** the concrete implementation MUST be placed in an adapter layer

### Requirement: Legacy compatibility layers MUST be treated as migration facades rather than primary implementation targets
If the repository keeps older module paths during a migration period, those paths MUST be treated as compatibility facades or re-export layers and MUST NOT remain the primary home for new core logic.

#### Scenario: Contributor touches a legacy compatibility module
- **WHEN** a contributor modifies a compatibility path retained for migration stability
- **THEN** that path MAY expose facades or re-exports for older imports
- **AND** new core logic MUST be implemented in the current hexagonal layer structure instead of being added directly to the compatibility module

### Requirement: Architecture governance documentation MUST stay aligned with enforced capabilities
The repository MUST maintain architecture guidance in project documentation so that contributor-facing guidance stays aligned with the current hexagonal architecture capabilities and migration rules.

#### Scenario: Architecture rules change
- **WHEN** a change adds or modifies repository-level architecture requirements
- **THEN** the affected contributor-facing documentation MUST be updated in the same change
- **AND** that documentation MUST NOT contradict the active OpenSpec capabilities
