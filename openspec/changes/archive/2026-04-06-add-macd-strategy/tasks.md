## 1. Strategy scaffolding

- [x] 1.1 Add a MACD trend strategy module under `src/strategies/trend/` that implements the existing `BaseStrategy` contract.
- [x] 1.2 Define and document the strategy input contract, default MACD parameters, and validation for the required `close` column.

## 2. Signal and position logic

- [x] 2.1 Implement MACD indicator calculation that produces `dif`, `dea`, and `histogram` from time-ordered close prices.
- [x] 2.2 Implement deterministic `buy` / `sell` / `hold` crossover signals, including the optional zero-axis filter for long entries.
- [x] 2.3 Implement long-only target position building with flat (`0`) and fully invested (`1`) states and safe handling for warm-up or invalid rows.

## 3. Verification and integration

- [x] 3.1 Add tests covering valid indicator output, missing `close` validation, bullish and bearish crossover behavior, zero-axis filtering, and warm-up or invalid-data handling.
- [x] 3.2 Add a minimal callable entry point or usage path so the MACD strategy can be consumed by research scripts or future backtest modules.
