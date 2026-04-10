## ADDED Requirements

### Requirement: System MUST provide a reusable A-share stock list fetcher based on AkShare
The system MUST provide a reusable implementation that fetches the A-share stock list from AkShare and makes the result available to other project modules.

#### Scenario: Strategy or data pipeline requests the stock universe
- **WHEN** a project module requests the A-share stock list
- **THEN** the system MUST fetch the list through an AkShare-based implementation
- **AND** the fetching logic MUST be reusable outside of a one-off notebook context

### Requirement: A-share stock list output MUST be normalized into stable fields
The fetched A-share stock list MUST be normalized into a stable project-facing structure that includes at least stock code, stock name, and market or exchange information.

#### Scenario: Caller consumes the fetched stock list
- **WHEN** a caller receives the normalized A-share stock list
- **THEN** each row MUST expose stable normalized fields for symbol, name, and market or exchange identity
- **AND** the caller MUST NOT be forced to depend directly on raw AkShare column names

### Requirement: Default A-share stock list MUST exclude ST and *ST stocks
The default stock list capability MUST exclude ST and *ST stocks from the returned A-share universe.

#### Scenario: Caller requests the default stock universe
- **WHEN** the caller uses the default A-share stock list behavior
- **THEN** rows representing ST or *ST stocks MUST be excluded from the result
- **AND** non-ST A-share stocks MUST remain eligible for inclusion

### Requirement: System MUST provide a script entrypoint for the filtered A-share stock list
The project MUST provide a script-level entrypoint so contributors can run the A-share stock list fetch and filtering flow from the command line.

#### Scenario: Contributor runs the stock list flow manually
- **WHEN** a contributor runs the supported command-line entrypoint for the A-share stock list
- **THEN** the project MUST execute the AkShare fetch and ST filtering logic
- **AND** the result MUST be inspectable or exportable from that script workflow
