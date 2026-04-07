## ADDED Requirements

### Requirement: Render candlestick and volume panels in one image
The system SHALL export a single PNG image that contains a candlestick price panel and a volume bar panel aligned on the same time axis for the selected K-line dataset.

#### Scenario: Export combined candlestick and volume image
- **WHEN** the user runs the K-line chart workflow with a valid normalized dataset containing `datetime`, `open`, `high`, `low`, `close`, and `volume`
- **THEN** the system writes one PNG artifact that includes a candlestick panel above a volume panel with both panels representing the same row sequence

#### Scenario: Support datasets without datetime column
- **WHEN** the input dataset contains `open`, `high`, `low`, `close`, and `volume` but omits `datetime`
- **THEN** the system MUST still export one PNG artifact using row order as the shared x-axis

### Requirement: Validate chart input before rendering
The system SHALL validate that chart input is non-empty and includes the required columns `open`, `high`, `low`, `close`, and `volume` before attempting to render the combined image.

#### Scenario: Reject empty input data
- **WHEN** the renderer receives an empty dataset
- **THEN** the system MUST fail with an explicit validation error instead of exporting a blank image

#### Scenario: Reject missing OHLCV columns
- **WHEN** the input dataset is missing any of `open`, `high`, `low`, `close`, or `volume`
- **THEN** the system MUST fail with an explicit validation error that identifies the missing requirement

### Requirement: Provide a CLI workflow for combined chart export
The system SHALL provide a script-level workflow that accepts a K-line CSV input and writes the combined candlestick-and-volume PNG to a deterministic output path or to a caller-provided output path.

#### Scenario: Use default report output path
- **WHEN** the user runs the workflow without specifying an explicit PNG destination
- **THEN** the system MUST generate the chart under the existing report/output convention and print the resolved chart path

#### Scenario: Respect explicit output path
- **WHEN** the user runs the workflow with an explicit PNG destination
- **THEN** the system MUST write the chart to that destination, creating parent directories as needed
