.PHONY: help venv install-dev test normalize macd-signal backtest-macd clean clean-reports

PYTHON ?= .\.venv\Scripts\python.exe
RAW_CSV ?= data/raw/600519_KLINE.csv
NORMALIZED_CSV ?= data/processed/600519_KLINE.normalized.csv
BACKTEST_START ?= 2025-01-01
BACKTEST_END ?= 2025-12-31
INITIAL_CAPITAL ?= 1000000
POSITION_SIZE ?= 0.5
FEE_RATE ?= 0.0001
STAMP_DUTY_RATE ?= 0.001
SLIPPAGE_RATE ?= 0.0005
LOT_SIZE ?= 100

help:
	@echo Available targets:
	@echo   make venv
	@echo   make install-dev
	@echo   make test
	@echo   make normalize RAW_CSV=data/raw/600519_KLINE.csv
	@echo   make macd-signal RAW_CSV=data/raw/600519_KLINE.csv
	@echo   make backtest-macd RAW_CSV=data/raw/600519_KLINE.csv BACKTEST_START=2025-01-01 BACKTEST_END=2025-12-31
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

macd-signal:
	$(PYTHON) scripts/run_macd_strategy.py $(RAW_CSV)

backtest-macd:
	$(PYTHON) scripts/backtest_macd.py $(RAW_CSV) --start-date $(BACKTEST_START) --end-date $(BACKTEST_END) --initial-capital $(INITIAL_CAPITAL) --position-size $(POSITION_SIZE) --fee-rate $(FEE_RATE) --stamp-duty-rate $(STAMP_DUTY_RATE) --slippage-rate $(SLIPPAGE_RATE) --lot-size $(LOT_SIZE)

clean-reports:
	@if exist outputs\\reports\\*.csv del /q outputs\\reports\\*.csv
	@if exist outputs\\reports\\*.png del /q outputs\\reports\\*.png

clean: clean-reports
	@if exist .pytest_tmp rmdir /s /q .pytest_tmp
	@if exist .tmp-python rmdir /s /q .tmp-python
	@if exist .cache\\matplotlib rmdir /s /q .cache\\matplotlib
