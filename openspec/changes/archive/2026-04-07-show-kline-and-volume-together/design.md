## Context

The repository already provides normalized K-line ingestion and `matplotlib`-based backtest chart export, but current charts focus on strategy diagnostics such as close price, indicators, capital, and trade markers. There is no dedicated utility for discretionary inspection of candlestick structure together with trading volume on the same time axis.

The existing plotting stack in `src/backtest/charting.py` already configures a headless `matplotlib` backend, Chinese-friendly fonts, output directory creation, and PNG export conventions. Reusing that stack keeps the new feature consistent with current reports and avoids bringing in a second plotting library for a narrow requirement.

## Goals / Non-Goals

**Goals:**
- Add a reusable renderer that produces a single PNG containing a candlestick panel and a volume panel aligned on the same x-axis.
- Accept normalized K-line input with `datetime`, `open`, `high`, `low`, `close`, and `volume` columns.
- Expose the capability through a simple script or CLI entry point that fits the repository's current report-generation workflow.
- Define deterministic validation and output behavior so tests can verify success and failure cases.

**Non-Goals:**
- Adding interactive charts, HTML outputs, or browser-based visualization.
- Changing the existing MACD or grid backtest chart layouts.
- Supporting every optional market field such as turnover, amount, or open interest in the first version.
- Introducing a new third-party candlestick library when the current `matplotlib` stack is sufficient.

## Decisions

### Reuse the existing `matplotlib` charting stack

The implementation will extend the current charting utilities instead of adding `mplfinance`, Plotly, or another dependency. This keeps deployment simple, preserves the repository's current font/backend handling, and allows the new renderer to share export conventions with backtest charts.

Alternative considered:
- Add a dedicated finance plotting dependency. Rejected because the required output is a static PNG with a small surface area, and a new dependency would increase maintenance cost without a clear functional advantage.

### Introduce a dedicated K-line plus volume renderer

The candlestick-and-volume chart will be implemented as a dedicated renderer rather than overloading `plot_strategy_backtest`. The existing backtest helper assumes strategy-specific panels, capital curves, and summary cards, which are not part of this feature. A focused renderer reduces branching and keeps the API clear: one function for strategy backtests, one function for raw market visualization.

Alternative considered:
- Generalize `plot_strategy_backtest` into a fully configurable plotting framework. Rejected because it expands the scope significantly and is unnecessary for a single new visualization workflow.

### Standardize input validation around normalized K-line columns

The new feature will require `open`, `high`, `low`, `close`, and `volume`, and it will use `datetime` when present for the shared x-axis. Missing required columns or empty input will raise explicit validation errors rather than silently downgrading to a line chart or skipping volume.

Alternative considered:
- Render partial charts when some columns are missing. Rejected because the user request is specifically about observing the relationship between candlesticks and volume; silent degradation would produce ambiguous results.

### Provide a script-level entry point for artifact generation

The feature will be exposed through a script under `scripts/` that accepts a raw or normalized CSV path, reuses the existing normalization flow when needed, and writes a PNG into the report/output area. This matches how current strategy and backtest workflows are invoked and makes the capability easy to automate from the command line or `Makefile`.

Alternative considered:
- Ship only a Python helper function. Rejected because the repository already favors script entry points for user-facing workflows.

## Risks / Trade-offs

- [Manual candlestick rendering is more verbose than using a finance library] → Keep the implementation narrowly scoped and cover it with renderer-level tests.
- [Large datasets may produce dense, harder-to-read candles and volume bars] → Preserve a clear default figure size and keep the initial scope focused on static analysis output rather than adaptive aggregation.
- [Raw CSVs may contain inconsistent encodings or Chinese headers] → Reuse the existing normalization path before rendering so the renderer only handles normalized column semantics.
- [Another chart entry point increases maintenance surface] → Share common path handling and plotting configuration with existing utilities instead of duplicating infrastructure.
