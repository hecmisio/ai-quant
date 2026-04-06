## 1. Strategy scaffolding

- [x] 1.1 Add a `GridStrategy` module under `src/strategies/` with a parameter model for `lower_bound`, `upper_bound`, `grid_count`, and `price_column`.
- [x] 1.2 Expose the new strategy through the relevant package `__init__` files so research code can import it consistently with existing strategies.
- [x] 1.3 Implement shared input preparation and validation for DataFrame input, required price column checks, and invalid grid parameter errors.

## 2. Core grid logic

- [x] 2.1 Implement fixed evenly spaced grid-level generation and expose grid metadata needed for downstream inspection.
- [x] 2.2 Implement deterministic price-bucket to `target_position` mapping with long-only stepped positions and boundary saturation at `0.0` and `1.0`.
- [x] 2.3 Implement signal generation so `buy`, `sell`, and `hold` are derived from changes in `target_position`, including direct multi-level jumps on a single row.
- [x] 2.4 Ensure invalid numeric rows emit safe fallback outputs while preserving input row order and index.

## 3. Verification and entry points

- [x] 3.1 Add unit tests covering valid grid construction, parameter validation, missing price columns, bucket-to-position mapping, boundary saturation, and invalid rows.
- [x] 3.2 Add tests for signal behavior when price crosses one grid, stays in the same grid, and jumps across multiple grids in one step.
- [x] 3.3 Add or update a callable script or usage path so the grid strategy can be executed in the same research workflow as existing strategies.
