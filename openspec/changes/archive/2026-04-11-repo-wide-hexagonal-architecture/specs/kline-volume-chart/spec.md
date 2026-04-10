## MODIFIED Requirements

### Requirement: Provide a CLI workflow for combined chart export
The system SHALL provide a script-level workflow that accepts a K-line CSV input and writes the combined candlestick-and-volume PNG to a deterministic output path or to a caller-provided output path, and that workflow MUST keep CLI concerns separate from normalization, validation, and rendering logic through the repository's adapter boundaries.

#### Scenario: Use default report output path
- **WHEN** the user runs the workflow without specifying an explicit PNG destination
- **THEN** the system MUST generate the chart under the existing report/output convention and print the resolved chart path

#### Scenario: Respect explicit output path
- **WHEN** the user runs the workflow with an explicit PNG destination
- **THEN** the system MUST write the chart to that destination, creating parent directories as needed
