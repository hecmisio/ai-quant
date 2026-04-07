## 1. Chart Rendering

- [x] 1.1 Add a dedicated renderer for combined candlestick and volume chart export using the existing `matplotlib` stack
- [x] 1.2 Add input validation for non-empty OHLCV data and shared x-axis handling with and without `datetime`

## 2. CLI Workflow

- [x] 2.1 Add a script entry point that accepts a K-line CSV input and exports the combined chart PNG
- [x] 2.2 Reuse the existing normalization and report-path conventions so the workflow supports default and explicit output paths

## 3. Verification

- [x] 3.1 Add unit tests for successful combined chart generation and deterministic output-path behavior
- [x] 3.2 Add unit tests for validation failures on empty input and missing required columns
