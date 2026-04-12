# ai-quant

AI-based quantitative strategy experiments. This repository is for research and engineering practice only and is not investment advice.

## Current Scope

The current repo includes:

- K-line CSV normalization for non-UTF-8 files and Chinese column names
- A-share stock-list fetching and Anne PostgreSQL ingestion
- Historical K-line fetching from AkShare and persistence into Anne `market_bars`
- K-line and volume chart export for normalized price data

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

## Database Bootstrap

The repository includes a local Anne database bootstrap based on `PostgreSQL 18.3`, `TimescaleDB 2.26.2`, and `pgvector`.

- `ANNE_POSTGRES_DB`: database name created on first initialization
- `ANNE_POSTGRES_USER`: database user created on first initialization
- `ANNE_POSTGRES_PASSWORD`: password for the database user
- `ANNE_POSTGRES_PORT`: host port mapped to the PostgreSQL container
- `ANNE_TIMESCALEDB_TELEMETRY`: TimescaleDB telemetry setting, default `off`

`docker compose` reads variables from a repository-root `.env` file automatically. For local setup, copy the example values into a root `.env` file or export the variables in your shell before starting the service.

Start the database:

```powershell
docker compose up -d --build anne-postgres
```

Verify the extensions:

```powershell
docker compose exec anne-postgres psql -U anne -d anne -c "SELECT extname, extversion FROM pg_extension WHERE extname IN ('timescaledb', 'vector') ORDER BY extname;"
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
- `make ingest-historical-kline EXCHANGE=SSE SYMBOL=600519 TIMEFRAME=1d ADJUSTMENT_TYPE=none START_DATE=2024-01-01 END_DATE=2024-12-31`
- `make clean-reports`
- `make clean`

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

## Ingest Historical K-line Data

Fetch provider-backed historical K-line bars for an existing Anne instrument and persist them into `market_bars`:

```powershell
.\.venv\Scripts\python.exe scripts/ingest_historical_kline.py --exchange SSE --symbol 600519 --timeframe 1d --adjustment-type none --start-date 2024-01-01 --end-date 2024-12-31
```

Or:

```powershell
make ingest-historical-kline EXCHANGE=SSE SYMBOL=600519 TIMEFRAME=1d ADJUSTMENT_TYPE=none START_DATE=2024-01-01 END_DATE=2024-12-31
```

Fetch all matching Anne instruments concurrently with a terminal progress bar:

```powershell
.\.venv\Scripts\python.exe scripts/ingest_historical_kline.py --all-instruments --instrument-type equity --instrument-status active --timeframe 1d --adjustment-type none --start-date 2024-01-01 --end-date 2024-12-31 --max-workers 8
```

Notes:

- The target instrument must already exist in Anne `instruments`.
- The first implementation fetches historical bars through AkShare.
- Supported v1 timeframes are `1d`, `1w`, and `1m`.
- Supported v1 adjustment types are `none`, `qfq`, and `hfq`.
- `--all-instruments` mode resolves targets from Anne `instruments`, fetches them concurrently, and prints a live progress bar plus a bulk summary.

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

- `src/domain/`: pure business rules and transformations
- `src/application/`: use cases and port definitions
- `src/adapters/`: inbound and outbound adapters such as CLI, AkShare, filesystem, and persistence
- `db/`: database infrastructure including ORM models, sessions, and SQL schema
- `src/data/`: compatibility facade for older imports, to be phased out
- `src/strategies/`: shared strategy contracts and compatibility namespaces
- `src/backtest/`: generic backtest utilities and plotting logic
- `scripts/`: executable entry points
- `tests/`: pytest test suite

## Architecture

The repository is moving toward a hexagonal architecture:

- `domain` contains pure business logic
- `application` contains use cases and ports
- `adapters` contain implementations for CLI, AkShare, filesystem, and persistence
- `db` contains SQLAlchemy models and session factories

Naming conventions:

- external data readers use `*Provider`
- persistence adapters use `*Gateway` by default and `*Repository` only when aggregate-oriented storage abstractions are needed
- CLI adapters live under `src/adapters/inbound/cli/` and expose `run_*_command`
- legacy paths such as `src/data/` are compatibility facades, not primary implementation targets

The detailed architectural constraints and migration priorities are documented in [docs/ai-quant/AI量化-六边形架构约束.md](docs/ai-quant/AI量化-六边形架构约束.md).
