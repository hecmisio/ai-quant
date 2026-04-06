# ai-quant

AI-based quantitative strategy experiments. This repository is for research and engineering practice only and is not investment advice.

## Current Scope

The current repo includes:

- K-line CSV normalization for non-UTF-8 files and Chinese column names
- A long-only MACD strategy
- MACD backtesting with capital, position sizing, fee, stamp duty, slippage, and A-share lot-size constraints
- Chart export with price, buy/sell execution points, MACD panel, capital curve, and summary cards

## Environment

Recommended Python version: `3.12`

Create and install the local environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Makefile Commands

The repo now includes a `Makefile` for common workflows.

Show available targets:

```powershell
make help
```

Common targets:

- `make venv`
- `make install-dev`
- `make test`
- `make normalize RAW_CSV=data/raw/600519_KLINE.csv`
- `make macd-signal RAW_CSV=data/raw/600519_KLINE.csv`
- `make backtest-macd RAW_CSV=data/raw/600519_KLINE.csv BACKTEST_START=2025-01-01 BACKTEST_END=2025-12-31`
- `make clean-reports`
- `make clean`

Default backtest parameters in the `Makefile`:

- `INITIAL_CAPITAL=1000000`
- `POSITION_SIZE=0.5`
- `FEE_RATE=0.0001`
- `STAMP_DUTY_RATE=0.001`
- `SLIPPAGE_RATE=0.0005`
- `LOT_SIZE=100`

## Data Normalization

Raw K-line CSV files can contain:

- non-UTF-8 encodings such as `gbk` / `gb18030`
- Chinese headers

Normalize them into UTF-8 and ASCII column names:

```powershell
.\.venv\Scripts\python.exe scripts\normalize_kline_csv.py data/raw/600519_KLINE.csv
```

Or:

```powershell
make normalize RAW_CSV=data/raw/600519_KLINE.csv
```

By default, the normalized file is written under `data/processed/`.

## Run MACD Signals

Generate MACD indicator and signal output from a CSV file:

```powershell
.\.venv\Scripts\python.exe scripts/run_macd_strategy.py data/raw/600519_KLINE.csv
```

Or:

```powershell
make macd-signal RAW_CSV=data/raw/600519_KLINE.csv
```

## Run MACD Backtest

Backtest MACD on a raw or normalized CSV:

```powershell
.\.venv\Scripts\python.exe scripts/backtest_macd.py data/raw/600519_KLINE.csv --start-date 2025-01-01 --end-date 2025-12-31 --initial-capital 1000000 --position-size 0.5
```

Or:

```powershell
make backtest-macd RAW_CSV=data/raw/600519_KLINE.csv BACKTEST_START=2025-01-01 BACKTEST_END=2025-12-31
```

The backtest outputs:

- result CSV under `outputs/reports/`
- chart PNG under `outputs/reports/`

## Cleanup

Remove generated report files:

```powershell
make clean-reports
```

Remove generated report files and local temporary caches:

```powershell
make clean
```

## Project Layout

- `src/data/`: CSV reading and normalization
- `src/strategies/trend/`: strategy implementations
- `src/backtest/`: backtest and plotting logic
- `scripts/`: executable entry points
- `tests/`: pytest test suite
