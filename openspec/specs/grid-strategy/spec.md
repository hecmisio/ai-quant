## ADDED Requirements

### Requirement: Grid strategy validates inputs and derives fixed grid levels
The system SHALL provide a grid strategy that accepts time-ordered market data in a `pandas.DataFrame` and requires a numeric price column named `close` by default. The strategy SHALL require `lower_bound`, `upper_bound`, and `grid_count` parameters, where `lower_bound` is less than `upper_bound` and `grid_count` is a positive integer. The strategy SHALL derive evenly spaced grid levels from those parameters and expose the derived spacing and level metadata in its output so downstream tests can inspect the grid definition.

#### Scenario: Build evenly spaced grid levels from valid parameters
- **WHEN** the strategy receives valid `lower_bound`, `upper_bound`, `grid_count`, and input data with a valid `close` column
- **THEN** the output includes deterministic grid metadata derived from evenly spaced levels between the lower and upper bounds

#### Scenario: Reject invalid grid parameters
- **WHEN** the strategy is initialized with `lower_bound` greater than or equal to `upper_bound`, or with a non-positive `grid_count`
- **THEN** the strategy MUST fail with an explicit validation error

#### Scenario: Reject missing price column
- **WHEN** the strategy receives input data without the configured price column
- **THEN** the strategy MUST fail with an explicit validation error instead of inferring another column implicitly

### Requirement: Grid strategy maps price buckets to stepped long-only target positions
The system SHALL convert the current price into a deterministic long-only `target_position` based on the bucket defined by the fixed grid levels. Prices at or below `lower_bound` SHALL map to `1.0`, prices at or above `upper_bound` SHALL map to `0.0`, and prices inside the range SHALL map to stepped positions that change in increments of `1 / grid_count`, with lower price buckets producing higher target positions.

#### Scenario: Increase target position as price moves into lower buckets
- **WHEN** the current price moves from a higher grid bucket into a lower grid bucket within the configured range
- **THEN** the resulting `target_position` increases by one or more grid steps

#### Scenario: Saturate at full position below lower bound
- **WHEN** the current price is less than or equal to the configured `lower_bound`
- **THEN** the strategy outputs `target_position` equal to `1.0`

#### Scenario: Saturate at zero position above upper bound
- **WHEN** the current price is greater than or equal to the configured `upper_bound`
- **THEN** the strategy outputs `target_position` equal to `0.0`

### Requirement: Grid strategy emits rebalance signals from target-position changes
The system SHALL emit deterministic rebalance signals from the change in `target_position` between consecutive rows. If the current `target_position` is greater than the previous valid position, the strategy MUST emit `buy`; if it is lower, the strategy MUST emit `sell`; otherwise it MUST emit `hold`.

#### Scenario: Emit buy when target position increases
- **WHEN** the current row maps to a higher `target_position` than the previous valid row
- **THEN** the strategy emits a `buy` signal for that row

#### Scenario: Emit sell when target position decreases
- **WHEN** the current row maps to a lower `target_position` than the previous valid row
- **THEN** the strategy emits a `sell` signal for that row

#### Scenario: Hold when price remains in the same bucket
- **WHEN** consecutive rows map to the same grid bucket and therefore the same `target_position`
- **THEN** the strategy emits `hold`

### Requirement: Grid strategy handles invalid rows and multi-level jumps safely
The system SHALL preserve the input index and row order in all outputs. If a row contains missing or non-numeric price data, the strategy MUST emit `hold` and `target_position` equal to `0.0` for that row. If a valid row jumps across multiple grid buckets in a single step, the strategy SHALL move directly to the final bucket's `target_position` on that row instead of requiring one intermediate row per crossed grid.

#### Scenario: Stay safe on invalid price rows
- **WHEN** the current row contains a missing or non-numeric value in the configured price column
- **THEN** the strategy emits `hold` and `target_position` equal to `0.0` for that row

#### Scenario: Rebalance directly across multiple crossed grids
- **WHEN** the current valid price moves from one bucket to another bucket that is more than one grid step away
- **THEN** the strategy updates `target_position` directly to the final bucket's stepped position on that row

#### Scenario: Preserve input order and index
- **WHEN** the strategy processes a valid time-ordered input frame
- **THEN** the output keeps the same row order and index as the input data
