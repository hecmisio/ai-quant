## 1. Architecture Governance

- [x] 1.1 Add or refine the repository-wide hexagonal architecture directories and shared conventions for `domain`, `application`, `adapters`, and `db`.
- [x] 1.2 Define and standardize provider, gateway, repository, or equivalent port naming conventions for external integrations.
- [x] 1.3 Mark `src/data` as an explicit compatibility facade and prevent new core logic from being added there.

## 2. Capability Alignment

- [x] 2.1 Refactor the A-share stock universe flow so its implementation and imports align with the provider adapter and domain normalization boundaries.
- [x] 2.2 Refactor the A-share stock list ingestion flow so its implementation and imports align with the application service and persistence gateway boundaries.
- [x] 2.3 Refactor K-line related CLI workflows so scripts remain thin entrypoints and the logic lives behind inbound or outbound adapters.

## 3. Incremental Repo Migration

- [x] 3.1 Identify the next priority modules outside the current A-share and K-line flows that should adopt the same hexagonal boundaries.
- [x] 3.2 Migrate at least one additional representative module or workflow onto the new structure without breaking existing behavior.
- [x] 3.3 Update compatibility imports, package exports, and tests so old call sites continue to work during the transition.

## 4. Documentation and Verification

- [x] 4.1 Update README and architecture guidance documents to reflect the enforced repository structure, migration policy, and port or adapter rules.
- [x] 4.2 Add or update tests that verify the migrated workflows still behave correctly through the new boundaries.
- [x] 4.3 Run the relevant automated checks and at least one end-to-end workflow through the new script -> adapter -> application -> adapter path.
