.PHONY: help venv install-dev test normalize ingest-historical-kline clean clean-reports

PYTHON ?= .\.venv\Scripts\python.exe
RAW_CSV ?= data/raw/600519_KLINE.csv
NORMALIZED_CSV ?= data/processed/600519_KLINE.normalized.csv
BACKTEST_START ?= 2025-01-01
BACKTEST_END ?= 2025-12-31
EXCHANGE ?= SSE
SYMBOL ?= 600519
TIMEFRAME ?= 1d
ADJUSTMENT_TYPE ?= none
START_DATE ?=
END_DATE ?=

help:
	@echo Available targets:
	@echo   make venv
	@echo   make install-dev
	@echo   make test
	@echo   make normalize RAW_CSV=data/raw/600519_KLINE.csv
	@echo   make ingest-historical-kline EXCHANGE=SSE SYMBOL=600519 TIMEFRAME=1d ADJUSTMENT_TYPE=none START_DATE=2024-01-01 END_DATE=2024-12-31
	@echo   make clean-reports
	@echo   make clean

venv:
	python -m venv .venv

install-dev:
	$(PYTHON) -m pip install -r requirements-dev.txt

test:
	$(PYTHON) -m pytest -q

normalize:
	$(PYTHON) scripts/normalize_kline_csv.py $(RAW_CSV) --output-csv $(NORMALIZED_CSV)

ingest-historical-kline:
	$(PYTHON) scripts/ingest_historical_kline.py --exchange $(EXCHANGE) --symbol $(SYMBOL) --timeframe $(TIMEFRAME) --adjustment-type $(ADJUSTMENT_TYPE) $(if $(START_DATE),--start-date $(START_DATE),) $(if $(END_DATE),--end-date $(END_DATE),)

clean-reports:
	@if exist outputs\\reports\\*.csv del /q outputs\\reports\\*.csv
	@if exist outputs\\reports\\*.png del /q outputs\\reports\\*.png

clean: clean-reports
	@if exist .pytest_tmp rmdir /s /q .pytest_tmp
	@if exist .tmp-python rmdir /s /q .tmp-python
	@if exist .cache\\matplotlib rmdir /s /q .cache\\matplotlib
