## ADDED Requirements

### Requirement: MACD strategy computes canonical indicator outputs
The system SHALL provide a MACD strategy that accepts time-ordered market data with a `close` price column and computes the canonical MACD outputs using configurable fast EMA, slow EMA, and signal EMA periods. The strategy SHALL expose at least `dif`, `dea`, and `histogram` in its signal output so downstream tests and backtests can inspect intermediate indicator values.

#### Scenario: Compute MACD fields from valid close prices
- **WHEN** the strategy receives a time-ordered dataset with a valid `close` column and enough rows to evaluate the configured EMA windows
- **THEN** the signal output includes `dif`, `dea`, and `histogram` columns aligned to the input index

#### Scenario: Reject missing close column
- **WHEN** the strategy receives input data without a `close` column
- **THEN** the strategy MUST fail with an explicit validation error instead of producing signals from implicit assumptions

### Requirement: MACD strategy emits deterministic trade signals
The system SHALL emit deterministic trade signals from MACD crossovers. By default, the strategy MUST emit a buy signal when `dif` crosses above `dea`, a sell signal when `dif` crosses below `dea`, and a hold signal otherwise. The strategy MUST support an optional zero-axis filter so implementations can restrict long entries to periods where `dif` is greater than or equal to zero.

#### Scenario: Buy on bullish crossover
- **WHEN** `dif` moves from less than or equal to `dea` to greater than `dea` on the current bar
- **THEN** the strategy emits a `buy` signal for that bar

#### Scenario: Sell on bearish crossover
- **WHEN** `dif` moves from greater than or equal to `dea` to less than `dea` on the current bar
- **THEN** the strategy emits a `sell` signal for that bar

#### Scenario: Block long entry below zero axis when filter enabled
- **WHEN** a bullish crossover occurs while the zero-axis filter is enabled and `dif` is below zero
- **THEN** the strategy emits `hold` instead of `buy`

### Requirement: MACD strategy builds long-only target positions
The system SHALL convert trade signals into long-only target positions. The first version MUST support only flat (`0`) and fully invested long (`1`) target positions, where buy transitions the target position to `1`, sell transitions it to `0`, and hold preserves the prior valid target position.

#### Scenario: Enter long after buy signal
- **WHEN** the current target position is `0` and the current bar emits `buy`
- **THEN** the target position for that bar becomes `1`

#### Scenario: Exit long after sell signal
- **WHEN** the current target position is `1` and the current bar emits `sell`
- **THEN** the target position for that bar becomes `0`

#### Scenario: Hold prior position on neutral signal
- **WHEN** the current bar emits `hold`
- **THEN** the target position remains equal to the previous valid target position

### Requirement: MACD strategy handles warm-up and invalid data safely
The system SHALL not open positions during warm-up or invalid data segments. If there is not enough valid history to compute configured MACD values, or if the current row contains invalid numeric inputs, the strategy MUST emit `hold` and target position `0` for that row until valid indicator computation resumes.

#### Scenario: Stay flat during warm-up
- **WHEN** the dataset has not yet accumulated enough history to compute the configured MACD values for a row
- **THEN** that row emits `hold` and target position `0`

#### Scenario: Stay flat on invalid numeric rows
- **WHEN** the current row contains missing or invalid price data needed for MACD calculation
- **THEN** that row emits `hold` and target position `0`
