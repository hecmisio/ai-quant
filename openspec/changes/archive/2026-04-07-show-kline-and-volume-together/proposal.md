## Why

The repository already normalizes K-line data and exports strategy backtest charts, but it does not provide a dedicated visualization that shows candlesticks and trading volume together in a single image. This makes it harder to inspect price action and volume confirmation side by side during discretionary analysis and strategy research.

## What Changes

- Add a new charting capability that renders OHLC candlesticks and aligned volume bars into one PNG image.
- Support reading normalized K-line data with `datetime`, `open`, `high`, `low`, `close`, and `volume` columns as the chart input.
- Provide a script or entry point that generates the combined chart artifact under the existing report/output workflow.
- Define validation and output behavior so the feature fails clearly on missing required columns or empty data.

## Capabilities

### New Capabilities
- `kline-volume-chart`: Render a single image that combines candlestick price data and corresponding volume bars on a shared time axis.

### Modified Capabilities
- None.

## Impact

- Affected code: chart rendering utilities, a new or updated CLI script under `scripts/`, and related tests.
- Affected outputs: PNG chart artifacts under the existing reports/output conventions.
- Dependencies: existing `matplotlib` stack can be reused; no new external dependency is required if candlesticks are drawn with the current plotting library.
