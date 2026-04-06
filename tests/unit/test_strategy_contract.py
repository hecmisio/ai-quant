"""Tests for the shared BaseStrategy contract."""

from __future__ import annotations

import pandas as pd
import pytest

from src.strategies.base import BaseStrategy


class MissingSignalStrategy(BaseStrategy):
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        return data.copy()

    def get_params(self) -> dict:
        return {}


class InvalidSignalValueStrategy(BaseStrategy):
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        frame = data.copy()
        frame["signal"] = ["enter"] * len(frame)
        return frame

    def get_params(self) -> dict:
        return {}


class MissingTargetPositionStrategy(BaseStrategy):
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        frame = data.copy()
        frame["signal"] = ["hold"] * len(frame)
        return frame

    def build_positions(self, signals: pd.DataFrame) -> pd.DataFrame:
        return signals.copy()

    def get_params(self) -> dict:
        return {}


def build_fixture() -> pd.DataFrame:
    return pd.DataFrame({"close": [1.0, 2.0, 3.0]})


def test_strategy_run_requires_signal_column() -> None:
    with pytest.raises(ValueError, match="must include 'signal' column"):
        MissingSignalStrategy().run(build_fixture())


def test_strategy_run_rejects_unknown_signal_values() -> None:
    with pytest.raises(ValueError, match="unsupported values"):
        InvalidSignalValueStrategy().run(build_fixture())


def test_strategy_run_requires_target_position_column() -> None:
    with pytest.raises(ValueError, match="must include 'target_position' column"):
        MissingTargetPositionStrategy().run(build_fixture())
